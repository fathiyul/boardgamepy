"""Wrapper for LLMAgent that captures all LLM interactions."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel
import time

from ..ai.agent import LLMAgent


class LoggedLLMAgent:
    """
    Wrapper for LLMAgent that captures all LLM interactions.

    Intercepts LLM calls to record:
    - Input messages (system + user prompts)
    - Output responses (structured output)
    - Model name
    - Timing metadata
    - Errors if they occur
    """

    def __init__(self, llm_agent: LLMAgent, model_name: str = "unknown"):
        """
        Wrap an LLMAgent with logging.

        Args:
            llm_agent: LLMAgent instance to wrap
            model_name: Name of the model being used
        """
        self.agent = llm_agent
        self.model_name = model_name
        self._last_llm_call: Optional[Dict[str, Any]] = None

    def get_action(self, game: Any, player: Any) -> BaseModel:
        """
        Get action with LLM call logging.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            BaseModel: Structured output from LLM

        Raises:
            Exception: If LLM call fails
        """
        # Build messages
        messages = self.agent.prompt_builder.build_messages(game, player)

        # Call LLM and time it
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)

        try:
            response = self.agent._structured_llm.invoke(messages)
            latency_ms = (time.time() - start_time) * 1000

            # Capture LLM call data
            self._last_llm_call = {
                "messages": messages,
                "response": response.model_dump()
                if isinstance(response, BaseModel)
                else response,
                "model": self.model_name,
                "timestamp": timestamp,
                "metadata": {
                    "latency_ms": latency_ms,
                    # Usage data would come from LLM response if available
                    "usage": getattr(response, "usage", None),
                },
            }

            return response

        except Exception as e:
            # Log error
            self._last_llm_call = {
                "messages": messages,
                "response": None,
                "model": self.model_name,
                "timestamp": timestamp,
                "error": str(e),
                "metadata": {"latency_ms": (time.time() - start_time) * 1000},
            }
            raise

    def decide(self, game: Any, player: Any) -> tuple:
        """
        Decide action (PlayerAgent protocol).

        Delegates to wrapped agent's decide method.

        Args:
            game: Game instance
            player: Player instance

        Returns:
            tuple: (Action class, params dict)
        """
        return self.agent.decide(game, player)

    def __getattr__(self, name):
        """Delegate all other attributes to wrapped agent."""
        return getattr(self.agent, name)
