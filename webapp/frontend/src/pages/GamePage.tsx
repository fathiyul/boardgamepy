import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import api from "../api/client";
import { GameMeta } from "../types";

const fetchGames = async (): Promise<GameMeta[]> => {
  const res = await api.get("/games");
  return res.data;
};

export default function GamePage() {
  const { game } = useParams();
  const navigate = useNavigate();
  const [numPlayers, setNumPlayers] = useState<number | "">("");
  const [humanSeats, setHumanSeats] = useState("0");
  const [codenamesSeat, setCodenamesSeat] = useState<number>(1);
  const [teamModelMap, setTeamModelMap] = useState<Record<string, string>>({});
  const codenamesSeats = [
    { idx: 0, team: "Red", role: "Spymaster" },
    { idx: 1, team: "Red", role: "Operatives" },
    { idx: 2, team: "Blue", role: "Spymaster" },
    { idx: 3, team: "Blue", role: "Operatives" },
  ];

  const { data: games } = useQuery({
    queryKey: ["games"],
    queryFn: fetchGames,
  });
  const meta = useMemo(
    () => games?.find((g) => g.slug === game),
    [games, game],
  );

  const [opponentModel, setOpponentModel] = useState("random");

  const createSession = useMutation({
    mutationFn: async () => {
      if (!meta) throw new Error("Game not found");
      const humanParsed = humanSeats
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .map((n) => Number(n))
        .filter((n) => !Number.isNaN(n));
      const res = await api.post(`/games/${meta.slug}/sessions`, {
        num_players: numPlayers || undefined,
        human_seats:
          meta.slug === "codenames"
            ? [codenamesSeat]
            : humanParsed.length
            ? humanParsed
            : [0],
        config:
          meta.slug === "rps"
            ? { opponent_model: opponentModel }
            : meta.slug === "codenames"
            ? { team_model_map: teamModelMap }
            : undefined,
      });
      return res.data;
    },
    onSuccess: (session) => {
      navigate(`/${session.game_slug}/${session.session_id}`);
    },
  });

  if (!meta) {
    return (
      <div className="container">
        <p>Game not found.</p>
      </div>
    );
  }

  return (
    <div className="container">
      <button className="button secondary" onClick={() => navigate("/")}>
        🏠 Home
      </button>
      <h1>{meta.title}</h1>
      <p>{meta.description}</p>
      {meta.slug === "rps" && (
        <div
          className="card"
          style={{ maxWidth: 720, display: "grid", gap: 12 }}
        >
          <h3>Rules (Strategic RPS)</h3>
          <ul style={{ margin: 0, paddingLeft: 18, color: "#475569" }}>
            <li>Best of 15 rounds, first to 10 points wins.</li>
            <li>
              Each round randomizes win points and lose penalties for
              Rock/Paper/Scissors.
            </li>
            <li>
              You pick first; AI responds immediately. Effects shown on the
              round cards.
            </li>
            <li>Health reaches 0 → instant loss.</li>
          </ul>
          <label style={{ display: "grid", gap: 6, maxWidth: 260 }}>
            Opponent model
            <select
              value={opponentModel}
              onChange={(e) => setOpponentModel(e.target.value)}
            >
              <option value="random">Random (local)</option>
              <option value="google/gemini-3-flash-preview">
                Gemini 3 Flash
              </option>
              <option value="anthropic/claude-haiku-4.5">
                Claude 4.5 Haiku
              </option>
              <option value="openai/gpt-4.1-mini">GPT 4.1 Mini</option>
              <option value="x-ai/grok-4.1-fast">Grok 4.1 Fast</option>
            </select>
          </label>
          <div className="flex" style={{ alignItems: "center", gap: 12 }}>
            <button
              className="button"
              onClick={() => createSession.mutate()}
              disabled={createSession.isPending}
            >
              {createSession.isPending ? "Starting…" : "Start Match"}
            </button>
            <span style={{ color: "#475569", fontSize: 13 }}>2 players</span>
          </div>
          {createSession.error && (
            <p style={{ color: "crimson" }}>
              Failed: {(createSession.error as any).message}
            </p>
          )}
        </div>
      )}
      {meta.slug === "codenames" && (
        <div
          className="card"
          style={{ maxWidth: 720, display: "grid", gap: 12 }}
        >
          <h3>Rules (Codenames)</h3>
          <ul style={{ margin: 0, paddingLeft: 18, color: "#475569" }}>
            <li>Teams: Red vs Blue with Spymaster + Operatives.</li>
            <li>Red goes first. First team to reveal all agents wins.</li>
            <li>Spymaster gives a one-word clue + number; Operatives guess that many cards.</li>
            <li>Assassin revealed or clue matches a codename = instant loss.</li>
          </ul>
          <div className="flex" style={{ gap: 12, flexWrap: "wrap" }}>
            <label style={{ display: "grid", gap: 6 }}>
              Your seat
              <select value={codenamesSeat} onChange={(e) => setCodenamesSeat(Number(e.target.value))}>
                {codenamesSeats.map((seat) => (
                  <option key={seat.idx} value={seat.idx}>
                    {seat.team} {seat.role}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div style={{ display: "grid", gap: 6 }}>
            <div style={{ color: "#475569", fontSize: 13 }}>Models by team/role</div>
            {codenamesSeats.filter((seat) => seat.idx !== codenamesSeat).map((seat) => (
              <label key={seat.idx} style={{ display: "grid", gap: 4 }}>
                {seat.team} {seat.role} model
                <select
                  value={teamModelMap[seat.idx] || "google/gemini-3-flash-preview"}
                  onChange={(e) =>
                    setTeamModelMap((prev) => ({ ...prev, [seat.idx]: e.target.value }))
                  }
                >
                  <option value="google/gemini-3-flash-preview">Gemini 3 Flash</option>
                  <option value="anthropic/claude-haiku-4.5">Claude 4.5 Haiku</option>
                  <option value="openai/gpt-4.1-mini">GPT 4.1 Mini</option>
                  <option value="x-ai/grok-4.1-fast">Grok 4.1 Fast</option>
                </select>
              </label>
            ))}
            <p style={{ color: "#475569", fontSize: 12 }}>
              Note: Your chosen seat will ignore the model and use your own input (future UI). Currently all seats AI unless selected as human.
            </p>
          </div>
          <div className="flex" style={{ alignItems: "center", gap: 12 }}>
            <button
              className="button"
              onClick={() => createSession.mutate()}
              disabled={createSession.isPending}
            >
              {createSession.isPending ? "Starting…" : "Start Match"}
            </button>
            <span style={{ color: "#475569", fontSize: 13 }}>4 players</span>
          </div>
          {createSession.error && (
            <p style={{ color: "crimson" }}>
              Failed: {(createSession.error as any).message}
            </p>
          )}
        </div>
      )}
      {!meta.playable && <p>This game is not yet playable in the web UI.</p>}
      {meta.playable && meta.slug !== "rps" && meta.slug !== "codenames" && (
        <div className="card" style={{ maxWidth: 520 }}>
          <h3>Start Session</h3>
          <p style={{ fontSize: 13, color: "#475569" }}>
            Leave fields blank to use defaults (2 players, you in seat 0).
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createSession.mutate();
            }}
            style={{ display: "grid", gap: 10 }}
          >
            <label>
              Number of players (optional)
              <input
                type="number"
                min={meta.min_players}
                max={meta.max_players}
                value={numPlayers}
                onChange={(e) =>
                  setNumPlayers(e.target.value ? Number(e.target.value) : "")
                }
                placeholder={`${meta.min_players}-${meta.max_players} default`}
              />
            </label>
            <label>
              Human seats (comma separated indices, 0-based)
              <input
                value={humanSeats}
                onChange={(e) => setHumanSeats(e.target.value)}
                placeholder="0 for you; others AI"
              />
            </label>
            <button
              className="button"
              type="submit"
              disabled={createSession.isPending}
            >
              {createSession.isPending ? "Starting…" : "Start Session"}
            </button>
            {createSession.error && (
              <p style={{ color: "crimson" }}>
                Failed: {(createSession.error as any).message}
              </p>
            )}
          </form>
        </div>
      )}
    </div>
  );
}
