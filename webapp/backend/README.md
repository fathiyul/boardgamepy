# Backend (FastAPI)

## Quick start

```bash
cd webapp/backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn webapp.backend.main:app --reload --port 8000
```

Defaults: SQLite at `./webapp.db`, CORS allows `http://localhost:5173`. Set `OPENROUTER_API_KEY` to use LLM opponents.

## Adding another game
1. Implement a `GameAdapter` in `webapp/backend/registry.py` for the new example.
2. Map slug → metadata, `create_game`, `configure_players`, `serialize_state`, `apply_action`.
3. Ensure you expose actions via `valid_actions_for_player` and provide serializable state/board views.
4. Add a placeholder meta entry if the frontend should list it but it’s not playable yet.

## Notes for LLM agents
- Use `boardgamepy` prompt builders and output schemas from each example.
- Keep prompts short: only current round info is needed for RPS; avoid feeding full history unless the game requires it.
