"""DixiQuote game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent
from boardgamepy.ui import terminal as term
from game import DixiQuoteGame
from data import load_situations
from prompts import (
    StorytellerChoosePromptBuilder,
    StorytellerQuotePromptBuilder,
    SubmitSituationPromptBuilder,
    VotePromptBuilder,
)
from actions import (
    ChooseSituationAction,
    GiveQuoteAction,
    SubmitSituationAction,
    VoteAction,
)
from config import config
import ui


class DixiQuoteRunner(GameRunner):
    """Runner for DixiQuote with phase-based gameplay."""

    def setup_ai_agents(self, game):
        """Configure AI agents based on current phase with per-player models."""
        phase = game.state.phase
        storyteller_idx = game.state.storyteller_idx

        for i, player in enumerate(game.players):
            llm, model_name = self.create_llm_for_player(i)
            short_name = self.logging_config.get_short_model_name(model_name)

            # Choose prompt builder based on phase and role
            if i == storyteller_idx:
                if phase == "choose_situation":
                    prompt_builder = StorytellerChoosePromptBuilder()
                    output_schema = ChooseSituationAction.OutputSchema
                elif phase == "give_quote":
                    prompt_builder = StorytellerQuotePromptBuilder()
                    output_schema = GiveQuoteAction.OutputSchema
                else:
                    # Storyteller doesn't act in other phases
                    continue
            else:
                if phase == "submit_situations":
                    prompt_builder = SubmitSituationPromptBuilder()
                    output_schema = SubmitSituationAction.OutputSchema
                elif phase == "vote":
                    prompt_builder = VotePromptBuilder()
                    output_schema = VoteAction.OutputSchema
                else:
                    # Other players don't act in storyteller phases
                    continue

            base_agent = LLMAgent(
                llm=llm, prompt_builder=prompt_builder, output_schema=output_schema
            )
            player.agent = LoggedLLMAgent(base_agent, model_name)
            player.name = short_name

    def run_phase(self, game, player, phase, game_logger):
        """Handle a single phase action."""
        state_before = copy.deepcopy(game.state)

        # Don't show hand during voting phase
        show_hand = phase != "vote"

        if self.ui:
            ui.refresh(game, show_hand=show_hand, player_idx=player.player_idx)

        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"{term.FG_RED}Error: {e}{term.RESET}")
            time.sleep(2)
            return False

        # Execute action based on phase
        if phase == "choose_situation":
            action = ChooseSituationAction()
            params = {"situation": llm_output.situation}
            print(
                f"{term.BOLD}{term.FG_YELLOW}[P-{player.player_idx}: {player.name} - Storyteller]{term.RESET} Choosing situation..."
            )
            print(f"  {term.DIM}(Hidden from other players){term.RESET}")

        elif phase == "give_quote":
            action = GiveQuoteAction()
            params = {"quote": llm_output.quote}
            print(f"{term.BOLD}{term.FG_YELLOW}[P-{player.player_idx}: {player.name} - Storyteller]{term.RESET} Giving quote...")
            print(f'  Quote: {term.FG_BRIGHT_YELLOW}"{llm_output.quote}"{term.RESET}')

        elif phase == "submit_situations":
            action = SubmitSituationAction()
            params = {"situation": llm_output.situation}
            print(f"{term.BOLD}{term.FG_CYAN}[P-{player.player_idx}: {player.name}]{term.RESET} Submitting situation...")
            print(f"  {term.DIM}(Hidden until voting){term.RESET}")

        elif phase == "vote":
            action = VoteAction()
            params = {"situation": llm_output.situation}
            print(f"{term.BOLD}{term.FG_CYAN}[P-{player.player_idx}: {player.name}]{term.RESET} Voting...")
            print(f"  {term.DIM}(Hidden until scoring){term.RESET}")

        else:
            return False

        if llm_output.reasoning:
            ui.render_reasoning(llm_output.reasoning)

        if action.validate(game, player, **params):
            action.apply(game, player, **params)

            state_after = copy.deepcopy(game.state)

            # Reset consecutive invalid actions on success
            game.state.consecutive_invalid_actions = 0

            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, "_last_llm_call"):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=player,
                    state_before=state_before,
                    state_after=state_after,
                    board_before=None,
                    board_after=None,
                    action=action,
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
            return True
        else:
            # Track consecutive invalid actions
            game.state.consecutive_invalid_actions += 1
            print(
                f"{term.FG_RED}Invalid action! "
                f"(Strike {game.state.consecutive_invalid_actions}/3){term.RESET}"
            )

            # Apply penalty after 3 consecutive failures
            if game.state.consecutive_invalid_actions >= 3:
                print(
                    f"{term.FG_YELLOW}Player P-{player.player_idx} penalized: "
                    f"-1 point and turn skipped{term.RESET}"
                )

                # Apply -1 point penalty (minimum 0)
                current_score = game.state.scores.get(player.player_idx, 0)
                game.state.scores[player.player_idx] = max(0, current_score - 1)

                # Mark as skipped
                game.state.skipped_players.add(player.player_idx)

                # Mark this phase as completed for this player
                if phase == "submit_situations":
                    # Skip submission phase - mark as submitted with empty
                    pass  # Don't add to submitted_situations
                elif phase == "vote":
                    # Skip voting phase
                    pass  # Don't add to votes

                # Reset counter and skip turn
                game.state.consecutive_invalid_actions = 0
                time.sleep(3)
                return True  # Return True to move to next player
            else:
                time.sleep(2)
                return False

    def run_loop(self, game, game_logger):
        """Custom game loop with phase management."""
        while not game.state.is_terminal():
            # Re-assign agents for current phase
            self.setup_ai_agents(game)

            # Handle scoring phase
            if game.state.phase == "scoring":
                if self.ui:
                    ui.refresh(game)

                # Calculate scores
                situation_scores = game.calculate_scores()

                # Show scoring results
                ui.render_scoring_results(game, situation_scores)
                time.sleep(5)

                # Start new round
                game.start_new_round()
                continue

            # Get current player
            player = game.get_current_player()
            if player is None:
                # No player for this phase, should not happen
                print(f"{term.FG_RED}Error: No current player for phase {game.state.phase}{term.RESET}")
                break

            # Run the phase action
            self.run_phase(game, player, game.state.phase, game_logger)
            time.sleep(1.0)

    def on_game_end(self, game):
        """Show final game screen."""
        ui.refresh(game)
        print()
        print(f"{term.BOLD}{term.FG_GREEN}GAME OVER!{term.RESET}")
        print()

        # Show reason for game end
        if game.state.scores and max(game.state.scores.values()) >= game.state.target_score:
            print(f"{term.FG_CYAN}Game ended: Target score reached!{term.RESET}")
        elif game.state.round_number > game.state.max_rounds:
            print(f"{term.FG_CYAN}Game ended: Max rounds reached!{term.RESET}")
        elif not game.deck:
            print(f"{term.FG_CYAN}Game ended: Deck exhausted!{term.RESET}")

        print()

        if game.state.winner_idx is not None:
            winner = game.players[game.state.winner_idx]
            winner_score = game.state.scores.get(game.state.winner_idx, 0)
            print(f"{term.FG_YELLOW}Winner: {winner.name} with {winner_score} points!{term.RESET}")
        else:
            print("No winner")

        print()


def main():
    """Main entry point with CLI argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(description="Play DixiQuote")
    parser.add_argument("--target", type=int, default=None, help="Target score to win")
    parser.add_argument("--target-score", type=int, default=None, help="Target score to win")
    parser.add_argument("--max-rounds", type=int, default=None, help="Maximum number of rounds")
    parser.add_argument("--num-players", type=int, default=4, help="Number of players (3-8)")
    args = parser.parse_args()

    # Load situation cards
    situations = load_situations()
    print(f"Loaded {len(situations)} situation cards")

    # Determine target score (--target takes precedence over --target-score)
    target_score = args.target if args.target is not None else args.target_score
    if target_score is None:
        target_score = config.target_score

    # Determine max rounds
    max_rounds = args.max_rounds if args.max_rounds is not None else config.max_rounds

    print(f"Game settings: {args.num_players} players, target score: {target_score}, max rounds: {max_rounds}")

    try:
        # Run game
        runner = DixiQuoteRunner(
            game_class=DixiQuoteGame,
            prompt_builder_class=StorytellerChoosePromptBuilder,
            output_schema=ChooseSituationAction.OutputSchema,
            ui_module=ui,
            game_dir=Path(__file__).parent,
        )
        runner.run(
            situations=situations,
            num_players=args.num_players,
            target_score=target_score,
            max_rounds=max_rounds,
        )

    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
