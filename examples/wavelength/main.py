"""Wavelength game using boardgamepy framework."""

import copy
import time
from pathlib import Path

from boardgamepy import GameRunner
from boardgamepy.ai import LLMAgent
from boardgamepy.logging import LoggedLLMAgent
from boardgamepy.ui import terminal as term
from game import WavelengthGame
from prompts import PsychicPromptBuilder, GuesserPromptBuilder, OpponentPromptBuilder
from actions import GiveClueAction, GuessPositionAction, PredictDirectionAction
from config import config
import ui


class WavelengthRunner(GameRunner):
    """Runner for Wavelength with phase-based gameplay and role-specific agents."""

    def setup_ai_agents(self, game):
        """Configure AI agents based on player roles."""
        llm, model_name = self.create_llm()

        psychic_builder = PsychicPromptBuilder()
        guesser_builder = GuesserPromptBuilder()
        opponent_builder = OpponentPromptBuilder()

        for player in game.players:
            if player.role == "Psychic":
                base_agent = LLMAgent(llm=llm, prompt_builder=psychic_builder,
                                      output_schema=GiveClueAction.OutputSchema)
            elif player.role == "Guesser":
                base_agent = LLMAgent(llm=llm, prompt_builder=guesser_builder,
                                      output_schema=GuessPositionAction.OutputSchema)
            elif player.role == "Opponent":
                base_agent = LLMAgent(llm=llm, prompt_builder=opponent_builder,
                                      output_schema=PredictDirectionAction.OutputSchema)
            else:
                continue
            player.agent = LoggedLLMAgent(base_agent, model_name)

    def run_phase(self, game, player, phase, game_logger):
        """Handle a single phase of the game."""
        state_before = copy.deepcopy(game.state)
        board_before = copy.deepcopy(game.board)

        if self.ui:
            self.ui.refresh(game)

        try:
            llm_output = player.agent.get_action(game, player)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
            return False

        if phase == "psychic_clue":
            action = GiveClueAction()
            params = {"clue": llm_output.clue}
            print(f"{term.BOLD}{term.FG_CYAN}[Psychic]{term.RESET} Giving clue...")
            print(f"  Clue: \"{term.FG_YELLOW}{llm_output.clue}{term.RESET}\"")
        elif phase == "team_guess":
            action = GuessPositionAction()
            params = {"position": llm_output.position}
            print(f"{term.BOLD}{term.FG_CYAN}[Team]{term.RESET} Making guess...")
            print(f"  Position: {term.FG_YELLOW}{llm_output.position}{term.RESET}")
        elif phase == "opponent_predict":
            action = PredictDirectionAction()
            params = {"prediction": llm_output.prediction}
            print(f"{term.BOLD}{term.FG_CYAN}[Opponent]{term.RESET} Predicting...")
            print(f"  Prediction: {term.FG_YELLOW}{llm_output.prediction.upper()}{term.RESET}")
        else:
            return False

        if llm_output.reasoning:
            print(f"  {term.DIM}Reasoning: {llm_output.reasoning}{term.RESET}")
        print()

        if action.validate(game, player, **params):
            action.apply(game, player, **params)

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
                    action_params=params,
                    action_valid=True,
                    llm_call_data=llm_call_data,
                )
            return True
        else:
            print("Invalid action!")
            time.sleep(2)
            return False

    def run_loop(self, game, game_logger):
        """Custom game loop with phases."""
        while not game.state.is_terminal():
            # Re-assign agents when roles change
            self.setup_ai_agents(game)

            player = game.get_current_player()
            phase = game.state.phase

            if phase == "reveal":
                if self.ui:
                    self.ui.refresh(game)
                ui.render_result(game)
                time.sleep(5)

                if game.state.is_over:
                    break

                game.start_new_round()
            else:
                if player:
                    self.run_phase(game, player, phase, game_logger)

            time.sleep(1.5)

    def on_game_end(self, game):
        """Show final game screen."""
        ui.render_game_end(game)


if __name__ == "__main__":
    WavelengthRunner.main(
        game_class=WavelengthGame,
        prompt_builder_class=PsychicPromptBuilder,  # Default, overridden per role
        output_schema=GiveClueAction.OutputSchema,
        ui_module=ui,
        game_dir=Path(__file__).parent,
        default_num_players=config.num_players,
    )()
