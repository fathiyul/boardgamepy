# Frontend (Vite + React)

## Quick start

```bash
cd webapp/frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev -- --host
```

Build: `npm run build`

## Pages
- `/` list of games
- `/rps` rules + opponent model selection
- `/rps/:sessionId` play session (WS + REST)

## Adding another game UI
1. Add a route under `src/pages` (e.g., `/<slug>` for lobby and `/<slug>/:sessionId` for play).
2. Use REST endpoints already exposed by backend: `/games/{slug}/sessions`, `/actions`, `/ws/sessions/{id}`.
3. Render actions dynamically from the `schema` returned by `/actions/{player_idx}`; prefer buttons/selects for enums.
4. Show board/state from `SessionStateResponse` (`state`, `board_view`).

Styling: `src/styles.css`, no framework; keep components small (see SessionPage for RPS).
