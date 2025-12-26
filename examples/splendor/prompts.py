"""Splendor game prompts for AI agents."""

from typing import TYPE_CHECKING

from boardgamepy.ai import PromptBuilder

if TYPE_CHECKING:
    from boardgamepy.core.player import Player
    from game import SplendorGame


class SplendorPromptBuilder(PromptBuilder):
    """Build prompts for Splendor AI agents."""

    def build_system_prompt(self) -> str:
        """System prompt with Splendor rules."""
        return """You are playing Splendor, a card development and gem collection game!

GAME RULES:
- Collect gem tokens to purchase development cards
- Development cards give permanent bonuses and prestige points
- First to 15 prestige points triggers the end game
- Player with most points after the final round wins

GEM TYPES:
- 💎 Diamond (White)
- 🔷 Sapphire (Blue)
- 🟢 Emerald (Green)
- 🔴 Ruby (Red)
- ⚫ Onyx (Black)
- 🟡 Gold (Wild, from reserving cards)

ACTIONS (choose ONE per turn):
1. **TAKE GEMS**:
   - Take 3 different colored gems, OR
   - Take 2 of the same color (if 4+ available)
   - Cannot take Gold this way
   - Max 10 gems total (return excess immediately)

2. **PURCHASE CARD**:
   - Pay the gem cost shown on the card
   - Your card bonuses reduce costs (permanent discounts!)
   - Can use Gold as wild for any color
   - Card goes to your collection (permanent bonus + points)
   - Display is refilled from deck

3. **RESERVE CARD**:
   - Take 1 card from display and hide it
   - Get 1 Gold token (if available)
   - Can purchase reserved cards later
   - Max 3 reserved cards
   - Good for blocking opponents or saving cards for later

DEVELOPMENT CARDS:
- **Tier 1**: Cheap, few points (0-1 pts)
- **Tier 2**: Moderate cost, some points (1-3 pts)
- **Tier 3**: Expensive, high points (3-5 pts)
- Each card provides a permanent gem bonus (discount on future purchases)

NOBLES:
- Worth 3 prestige points
- Automatically visit you if you have required bonuses
- Example: Need 4 Diamond + 4 Sapphire bonuses (from cards)
- You get ONE noble per turn (if you qualify for multiple, choose one)

WINNING:
- First to 15 points triggers final round
- Everyone gets one more turn
- Highest total points wins
- Tiebreaker: Fewest cards purchased

STRATEGY TIPS:
1. **Early game**: Focus on cheap tier 1 cards to build bonuses
2. **Engine building**: Get bonuses in 2-3 colors for synergy
3. **Mid game**: Leverage bonuses to buy tier 2-3 cards cheaply
4. **Noble targeting**: Plan card purchases to attract nobles (free 3 points!)
5. **Reservation**: Block opponents from key cards or save expensive ones
6. **Gold management**: Gold is versatile but limited (5 total)
7. **Gem efficiency**: Don't hoard gems, convert to cards for permanent bonuses
8. **10 gem limit**: Plan purchases to avoid wasting gems

OUTPUT FORMAT:
You must choose ONE action type:

**Option 1 - Take Gems:**
{
  "action_type": "take_gems",
  "gem1": "Diamond",  // First gem
  "gem2": "Sapphire",  // Second gem (null if taking 2 of same)
  "gem3": "Emerald",  // Third gem (null if taking 2 of same)
  "take_two": false,  // true to take 2 of gem1 (requires 4+ available)
  "reasoning": "Your strategic thinking"
}

**Option 2 - Purchase Card:**
{
  "action_type": "purchase",
  "card_id": 123,  // Card ID number
  "from_reserved": false,  // true if buying from your reserved cards
  "reasoning": "Your strategic thinking"
}

**Option 3 - Reserve Card:**
{
  "action_type": "reserve",
  "card_id": 123,  // Card ID to reserve
  "tier": 2,  // Tier of the card (1, 2, or 3)
  "reasoning": "Your strategic thinking"
}
"""

    def build_user_prompt(self, game: "SplendorGame", player: "Player") -> str:
        """Build user prompt with current game state."""
        from boardgamepy.protocols import SimpleViewContext

        player_idx = int(player.team.split()[-1]) - 1
        context = SimpleViewContext(player=player, game_state=game.state)
        board_view = game.board.get_prompt_view(context)

        # Analyze affordable cards
        affordable_cards = []
        for card in (
            game.board.tier1_display + game.board.tier2_display + game.board.tier3_display
        ):
            if game.board.can_afford_card(player_idx, card):
                affordable_cards.append(card)

        for card in game.board.player_reserved[player_idx]:
            if game.board.can_afford_card(player_idx, card):
                affordable_cards.append(card)

        # Build prompt
        parts = [
            f"Turn {game.state.round_number}",
            "",
            board_view,
            "",
        ]

        # Your status
        your_points = game.board.get_player_points(player_idx)
        your_nobles = game.state.player_nobles.get(player_idx, [])
        your_bonuses = game.board.get_player_bonuses(player_idx)
        your_total_gems = game.board.get_total_gems(player_idx)

        parts.append(f"Your Points: {your_points}")
        if your_nobles:
            parts.append(f"Your Nobles: {len(your_nobles)} (worth {len(your_nobles) * 3} pts)")
        parts.append(f"Your Bonuses: {dict((k.value, v) for k, v in your_bonuses.items() if v > 0)}")
        parts.append(f"Total Gems: {your_total_gems}/10")
        parts.append("")

        # Affordable cards
        if affordable_cards:
            parts.append("💰 You can afford:")
            for card in affordable_cards[:5]:  # Show first 5
                parts.append(f"  - {card}")
            parts.append("")

        # Noble opportunities
        qualifying_nobles = game.board.check_nobles(player_idx)
        if qualifying_nobles:
            parts.append("👑 You qualify for nobles!")
            for noble in qualifying_nobles:
                parts.append(f"  - {noble}")
            parts.append("")

        # Check if close to nobles
        for noble in game.board.nobles:
            if noble in qualifying_nobles:
                continue
            bonuses_needed = []
            for gem, required in noble.requirements.items():
                current = your_bonuses.get(gem, 0)
                if current < required:
                    bonuses_needed.append(f"{required - current} more {gem.value}")
            if bonuses_needed and len(bonuses_needed) <= 2:
                parts.append(f"🎯 Close to {noble}: Need {', '.join(bonuses_needed)}")

        parts.append("")

        # Opponent status
        parts.append("Opponents:")
        for i in range(game.board.num_players):
            if i == player_idx:
                continue
            opp_points = game.board.get_player_points(i)
            opp_nobles = game.state.player_nobles.get(i, [])
            opp_bonuses = game.board.get_player_bonuses(i)
            bonus_str = ", ".join(f"{v}{k.value[0]}" for k, v in opp_bonuses.items() if v > 0)
            parts.append(
                f"  Player {i + 1}: {opp_points} pts, {len(opp_nobles)} nobles ({bonus_str})"
            )

        parts.append("")

        if game.state.final_round_triggered:
            parts.append("⚠️ FINAL ROUND! Someone reached 15 points. Make your last move count!")
            parts.append("")

        parts.append("What action do you take?")

        return "\n".join(parts)

    def build_messages(self, game: "SplendorGame", player: "Player") -> list[dict]:
        """Build message list for LLM."""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(game, player)},
        ]
