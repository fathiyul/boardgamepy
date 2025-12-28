"""Codenames game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent
from game import CodenamesGame
from data import load_codenames
from prompts import SpymasterPromptBuilder, OperativesPromptBuilder
from actions import ClueAction, GuessAction, PassAction
import ui


class CodenamesRunner(GameRunner):
    """Runner for Codenames with role-based agents and custom turn logic."""

    def setup_ai_agents(self, game):
        """Configure AI agents based on player roles."""
        llm, model_name = self.create_llm()

        for player in game.players:
            if player.role == "Spymaster":
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=SpymasterPromptBuilder(),
                    output_schema=ClueAction.OutputSchema,
                )
            else:  # Operatives
                base_agent = LLMAgent(
                    llm=llm,
                    prompt_builder=OperativesPromptBuilder(),
                    output_schema=GuessAction.OutputSchema,
                )
            player.agent = LoggedLLMAgent(base_agent, model_name)

    def run_turn(self, game, player, game_logger):
        """Custom turn handling for role-based actions."""
        state_before = copy.deepcopy(game.state)

        # Determine view mode and refresh UI
        mode = "spymaster" if player.role == "Spymaster" else "operatives"
        ui.refresh(game, mode, show_history=True)

        # Get action based on role
        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error getting action: {e}")
            time.sleep(2)
            return False

        if player.role == "Spymaster":
            action = ClueAction()
            params = {"clue": llm_output.clue, "count": llm_output.count}

            clue_colored = ui.term.colorize(
                f"{llm_output.clue} (Count: {llm_output.count})",
                fg=ui._team_fg(player.team)
            )
            ui.render_message(player.team, "Spymaster", clue_colored)
            ui.render_reasoning(llm_output.reasoning)
        else:  # Operatives
            if llm_output.action == "pass":
                action = PassAction()
                params = {}
                ui.render_message(player.team, "Operatives", "PASS")
            else:
                action = GuessAction()
                params = {"codename": llm_output.codename}
            ui.render_reasoning(llm_output.reasoning)

        if action.validate(game, player, **params):
            result = action.apply(game, player, **params)
            state_after = copy.deepcopy(game.state)

            # Log turn
            if game_logger.enabled:
                llm_call_data = None
                if hasattr(player.agent, '_last_llm_call'):
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

            game.state.consecutive_invalid_actions = 0

            # Show result for guesses
            if isinstance(action, GuessAction) and result:
                ui.render_guess_result(player.team, params["codename"], result)

            return True
        else:
            # Invalid action handling
            game.state.consecutive_invalid_actions += 1
            ui.render_message(
                player.team,
                player.role,
                f"Invalid action! (Strike {game.state.consecutive_invalid_actions}/3)",
                kind="warn"
            )

            if game.state.consecutive_invalid_actions >= 3:
                game.state.is_over = True
                game.state.winner = "Blue" if player.team == "Red" else "Red"
                ui.render_message(
                    None, "PENALTY",
                    f"{player.team} made 3 consecutive invalid actions and loses!",
                    kind="error"
                )

            time.sleep(2)
            return False

    def run_loop(self, game, game_logger):
        """Custom game loop with turn limit."""
        turn_count = 0
        max_turns = 100

        while not game.state.is_terminal() and turn_count < max_turns:
            turn_count += 1
            player = game.get_current_player()
            if player is None:
                break

            self.run_turn(game, player, game_logger)
            time.sleep(0.3)

        if turn_count >= max_turns:
            ui.render_message(None, "GAME", "Turn limit reached", kind="warn")

    def on_game_start(self, game):
        """Load codenames data during setup."""
        pass  # Already loaded via game.setup()

    def on_game_end(self, game):
        """Show final game screen."""
        ui.refresh(game, "operatives", show_history=True)
        winner = game.state.get_winner()
        if winner:
            ui.render_message(None, "GAME OVER", f"Winner: {winner}", kind="success")
        else:
            ui.render_message(None, "GAME OVER", "No winner", kind="info")


def main():
    """Main entry point."""
    try:
        codenames = load_codenames()
        runner = CodenamesRunner(
            game_class=CodenamesGame,
            prompt_builder_class=SpymasterPromptBuilder,  # Default, overridden in setup
            output_schema=ClueAction.OutputSchema,
            ui_module=ui,
            game_dir=Path(__file__).parent,
        )
        runner.run(codenames=codenames)
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
