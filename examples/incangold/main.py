"""Incan Gold game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from game import IncanGoldGame
from prompts import IncanGoldPromptBuilder
from actions import MakeDecisionAction
from config import config
import ui


class IncanGoldRunner(GameRunner):
    """Runner for Incan Gold with round-based exploration."""

    def collect_decisions(self, game, game_logger):
        """Collect decisions from all players still in temple."""
        action = MakeDecisionAction()

        for player_idx in sorted(game.board.in_temple):
            if player_idx in game.state.decisions:
                continue

            player = game.players[player_idx]
            state_before = copy.deepcopy(game.state)
            board_before = copy.deepcopy(game.board)

            if self.ui:
                self.ui.refresh(game)
            ui.render_decision_prompt(game, player_idx)

            try:
                llm_output = player.agent.get_action(game, player)
            except Exception as e:
                print(f"Error getting decision: {e}")
                time.sleep(2)
                llm_output = MakeDecisionAction.OutputSchema(
                    decision="return", reasoning="Error occurred, playing safe"
                )

            if action.validate(game, player, decision=llm_output.decision):
                ui.render_decision(player.team, llm_output.decision, llm_output.reasoning)
                action.apply(game, player, decision=llm_output.decision)

                state_after = copy.deepcopy(game.state)
                board_after = copy.deepcopy(game.board)

                if game_logger.enabled:
                    llm_call_data = None
                    if hasattr(player.agent, '_last_llm_call'):
                        llm_call_data = player.agent._last_llm_call
                        player.agent._last_llm_call = None

                    game_logger.log_turn(
                        player=player,
                        state_before=state_before,
                        state_after=state_after,
                        board_before=board_before,
                        board_after=board_after,
                        action=action,
                        action_params={"decision": llm_output.decision},
                        action_valid=True,
                        llm_call_data=llm_call_data,
                    )
            else:
                print(f"Invalid decision from {player.team}, defaulting to return")
                action.apply(game, player, decision="return")

            time.sleep(0.5)

    def reveal_and_resolve_card(self, game):
        """Reveal next card and resolve effects. Returns True if round continues."""
        card = game.board.reveal_card()

        if not card:
            print("The deck is empty! All explorers must return!")
            return False

        if self.ui:
            self.ui.refresh(game)
        ui.render_card_reveal(card, game)
        time.sleep(2)

        if game.board.did_temple_collapse():
            print(f"\n{card.hazard.value} appeared twice! Temple has collapsed!")
            print("All explorers lose their carried gems!")
            game.board.players_lose_temp_gems(game.board.in_temple)
            time.sleep(2)
            return False

        if card.is_treasure:
            game.board.distribute_treasure_to_explorers(card.value)

        return True

    def distribute_to_returners(self, game):
        """Distribute gems and artifacts to players returning."""
        if not game.board.returned_this_turn:
            return

        artifacts_on_path = [c for c in game.board.revealed_path if c.is_artifact]

        if artifacts_on_path and len(game.board.returned_this_turn) == 1:
            for artifact in artifacts_on_path:
                player_idx = game.board.give_artifact_to_sole_returner(artifact)
                if player_idx is not None:
                    print(f"\nPlayer {player_idx + 1} is the SOLE RETURNER and claims {artifact}!")
                    time.sleep(1.5)
            game.board.revealed_path = [c for c in game.board.revealed_path if not c.is_artifact]

        ui.render_distribution(game, game.board.returned_this_turn)
        game.board.distribute_gems_to_returners()

    def run_round(self, game, game_logger):
        """Run a single round of Incan Gold."""
        print(f"\n{'=' * 70}")
        print(f"ROUND {game.state.current_round}/{game.state.total_rounds} - Temple Exploration Begins!")
        print(f"{'=' * 70}\n")
        time.sleep(2)

        while not game.board.is_round_over():
            game.state.phase = "decide"
            game.state.decisions = {}

            if not game.board.in_temple:
                break

            self.collect_decisions(game, game_logger)
            game.process_decisions()
            self.distribute_to_returners(game)
            game.board.returned_this_turn = set()

            if not game.board.in_temple:
                break

            game.state.phase = "reveal"
            if not self.reveal_and_resolve_card(game):
                break

            time.sleep(1)

        if self.ui:
            self.ui.refresh(game)
        ui.render_round_end(game)
        time.sleep(3)

    def run_loop(self, game, game_logger):
        """Custom game loop with multiple rounds."""
        if self.ui:
            self.ui.refresh(game)
        time.sleep(2)

        while not game.state.is_terminal():
            self.run_round(game, game_logger)
            game.end_round()

    def on_game_end(self, game):
        """Show final game screen."""
        ui.render_game_end(game)


if __name__ == "__main__":
    IncanGoldRunner.main(
        game_class=IncanGoldGame,
        prompt_builder_class=IncanGoldPromptBuilder,
        output_schema=MakeDecisionAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
