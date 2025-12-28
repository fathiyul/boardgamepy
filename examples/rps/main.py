"""Run Strategic Rock Paper Scissors with AI players."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from strategy_game import StrategyRPSGame
from prompts_strategy import StrategyRPSPromptBuilder
from actions import StrategyChooseAction
import ui


class RPSRunner(GameRunner):
    """Runner for Strategic RPS with custom turn logic."""

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for RPS."""
        # Refresh UI
        if self.ui:
            self.ui.refresh(game)

        # Show player's turn
        player_num = 1 if player == game.players[0] else 2
        ui.render_turn_prompt(player.name, player_num)

        # Get action from AI
        action = StrategyChooseAction()
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            return False

        # Show AI choice and reasoning
        ui.render_ai_choice(llm_output.choice, llm_output.reasoning)

        # Capture board before
        board_before = copy.deepcopy(game.board)

        # Validate and apply
        if action.validate(game, player, choice=llm_output.choice):
            action.apply(game, player, choice=llm_output.choice)

            # Capture board after
            board_after = copy.deepcopy(game.board)

            # Log turn
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
                    llm_call_data = player.agent._last_llm_call
                    player.agent._last_llm_call = None

                game_logger.log_turn(
                    player=player,
                    state_before=game.state,
                    state_after=game.state,
                    board_before=board_before,
                    board_after=board_after,
                    action=action,
                    action_params={"choice": llm_output.choice},
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
            return True
        else:
            print("   Invalid choice!")
            return False

    def run_loop(self, game, game_logger):
        """Custom game loop with turn limit."""
        turn_count = 0
        max_turns = 100

        while not game.state.is_terminal() and turn_count < max_turns:
            turn_count += 1
            player = game.get_current_player()

            if player is None:
                continue

            success = self.run_turn(game, player, game_logger)
            if success:
                time.sleep(1)

        if turn_count >= max_turns:
            print("\nTurn limit reached!")

    def on_game_end(self, game):
        """Custom game over screen."""
        if self.ui:
            self.ui.refresh(game)
        ui.render_game_over(game)


if __name__ == "__main__":
    RPSRunner.main(
        game_class=StrategyRPSGame,
        prompt_builder_class=StrategyRPSPromptBuilder,
        output_schema=StrategyChooseAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
    )()
