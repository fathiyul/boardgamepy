import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../api/client';
import { SessionEvent, SessionState, ActionSchema } from '../types';
import { useSessionStore } from '../stores/useSessionStore';

function StatCard({ title, value, highlight, valueColor }: { title: string; value: string; highlight?: boolean; valueColor?: string }) {
  return (
    <div
      className="card"
      style={{
        padding: 12,
        minWidth: 160,
        border: highlight ? '2px solid #22c55e' : undefined,
      }}
    >
      <div style={{ fontSize: 12, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5 }}>{title}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: valueColor }}>{value}</div>
    </div>
  );
}

function renderEvent(ev: SessionEvent) {
  if (ev.type === 'action_applied') {
    return (
      <div>
        <strong>Turn {ev.turn}</strong> – {ev.action} {JSON.stringify(ev.params)}
      </div>
    );
  }
  if (ev.type === 'game_over') {
    return <div style={{ color: '#16a34a' }}>Game over</div>;
  }
  if (ev.type === 'session_state') {
    return <div>State sync</div>;
  }
  if (ev.type === 'error') {
    return <div style={{ color: 'crimson' }}>Error: {ev.message}</div>;
  }
  return <div>{JSON.stringify(ev)}</div>;
}

function isTurnOver(state: SessionState | null, humanIdx: number) {
  if (!state || !state.state) return true;
  if (state.state.game_over) return true;
  const p1 = state.state.player1_choice;
  const p2 = state.state.player2_choice;
  if (humanIdx === 0) return p1 !== null && p1 !== undefined;
  if (humanIdx === 1) return p2 !== null && p2 !== undefined;
  return false;
}

const BEATS: Record<string, string[]> = {
  rock: ['scissors'],
  paper: ['rock'],
  scissors: ['paper'],
};

function computeWinner(p1: string | null | undefined, p2: string | null | undefined) {
  if (!p1 || !p2) return null;
  if (p1 === p2) return 'Tie';
  return BEATS[p1]?.includes(p2) ? 'Player 1' : 'Player 2';
}

function formatOutcome(choice: string, isWinner: boolean, mapping: Record<string, any> | undefined) {
  const eff = mapping?.[choice];
  if (!eff) return '';
  if (isWinner) return `(+${eff.win_points} pts)`;
  if (eff.lose_type === 'none') return '(0)';
  if (eff.lose_type === 'points') return `(-${eff.lose_effect} pts)`;
  if (eff.lose_type === 'health') return `(-${eff.lose_effect} ♥)`;
  return '';
}

function isGameOver(state: any) {
  return Boolean(state?.game_over || state?.is_over);
}

function sessionWinnerLabel(state: any) {
  const isOver = state?.game_over || state?.is_over;
  if (!isOver) return null;
  if (state.winner === 'Player 1') return 'You win';
  if (state.winner === 'Player 2') return 'Opponent wins';
  if (state.winner) return `${state.winner} wins`;
  return 'Game over';
}

function resultEmoji(cardType?: string, team?: string) {
  if (cardType === 'Assassin') return '☠️';
  if (cardType === 'Civilian') return '🫥';
  if (team && cardType === team) return '❇️';
  return '💥';
}

function teamColor(team?: string) {
  if (team === 'Red') return '#dc2626';
  if (team === 'Blue') return '#2563eb';
  return '#0f172a';
}

function formatCodenamesHistoryEntry(entry: Record<string, any>) {
  const round = entry.round ? `R${entry.round}: ` : '';
  if (entry.type === 'clue') {
    return (
      <>
        {round}
        <span style={{ color: teamColor(entry.team), fontWeight: 700 }}>{entry.team}</span> Spymaster → {entry.clue} {entry.count}
      </>
    );
  }
  if (entry.type === 'guess') {
    const emoji = resultEmoji(entry.card_type, entry.team);
    return (
      <>
        {round}
        <span style={{ color: teamColor(entry.team), fontWeight: 700 }}>{entry.team}</span> Operatives: {entry.codename} {emoji}
      </>
    );
  }
  if (entry.type === 'pass') {
    return (
      <>
        {round}
        <span style={{ color: teamColor(entry.team), fontWeight: 700 }}>{entry.team}</span> Operatives PASSED
      </>
    );
  }
  return (
    <>
      {round}
      {entry.player || 'Unknown'} {entry.type || 'action'}
    </>
  );
}

function latestClueForTeam(history: Array<Record<string, any>>, team?: string) {
  if (!team) return null;
  for (let i = history.length - 1; i >= 0; i -= 1) {
    const entry = history[i];
    if (entry.type === 'clue' && entry.team === team) return entry;
  }
  return null;
}

function codenamesRoleFromPlayer(player?: { name?: string; idx?: number; team?: string }) {
  const name = (player?.name || '').toLowerCase();
  if (name.includes('spymaster')) return 'Spymaster';
  if (name.includes('operatives')) return 'Operatives';
  if (player?.idx === 0 || player?.idx === 2) return 'Spymaster';
  if (player?.idx === 1 || player?.idx === 3) return 'Operatives';
  return null;
}

const fetchSession = async (slug: string, id: string): Promise<SessionState> => {
  const res = await api.get(`/games/${slug}/sessions/${id}`);
  return res.data;
};

const fetchActions = async (slug: string, id: string, playerIdx: number): Promise<ActionSchema[]> => {
  const res = await api.get(`/games/${slug}/sessions/${id}/actions/${playerIdx}`);
  return res.data;
};

export default function SessionPage() {
  const { game, sessionId } = useParams();
  const navigate = useNavigate();
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const { state, setState, pushEvent, events } = useSessionStore();

  const { data: sessionData, isLoading } = useQuery({
    queryKey: ['session', game, sessionId],
    queryFn: () => fetchSession(game!, sessionId!),
    enabled: Boolean(game && sessionId),
    onSuccess: (data) => setState(data),
  });

  const humanPlayerIdx = useMemo(() => {
    const players = sessionData?.players || [];
    const human = players.find((p) => p.human) || players[0];
    return human?.idx ?? 0;
  }, [sessionData]);

  const actionsQuery = useQuery({
    queryKey: ['actions', game, sessionId, humanPlayerIdx],
    queryFn: () => fetchActions(game!, sessionId!, humanPlayerIdx),
    enabled: Boolean(game && sessionId),
  });

  useEffect(() => {
    if (!game || !sessionId) return;
    const apiBase = import.meta.env.VITE_API_URL || window.location.origin.replace(/:\d+$/, ':8000');
    const wsUrl = apiBase.replace(/^http/, 'ws') + `/ws/sessions/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (msg) => {
      try {
        const data: SessionEvent = JSON.parse(msg.data);
        pushEvent(data);
      } catch (e) {
        console.error('ws parse error', e);
      }
    };
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);
    wsRef.current = ws;
    return () => {
      ws.close();
    };
  }, [game, sessionId, pushEvent]);

  const actionMutation = useMutation({
    mutationFn: async (payload: Record<string, any>) => {
      const res = await api.post(`/games/${game}/sessions/${sessionId}/action`, {
        player_idx: humanPlayerIdx,
        action: payload.action,
        params: payload.params,
      });
      return res.data;
    },
  });

  const opponentModelFromName = (name?: string) => {
    const n = (name || '').toLowerCase();
    if (n.includes('gemini')) return 'google/gemini-3-flash-preview';
    if (n.includes('claude')) return 'anthropic/claude-haiku-4.5';
    if (n.includes('gpt') || n.includes('mini')) return 'openai/gpt-4.1-mini';
    if (n.includes('grok')) return 'x-ai/grok-4.1-fast';
    return 'random';
  };

  const playAgainMutation = useMutation({
    mutationFn: async () => {
      const model = opponentModelFromName(sessionData?.players?.[1]?.name);
      const res = await api.post(`/games/${game}/sessions`, {
        human_seats: [0],
        config: { opponent_model: model },
      });
      return res.data;
    },
    onSuccess: (session) => navigate(`/${session.game_slug}/${session.session_id}`),
  });

  const action = actionsQuery.data?.[0];
  const actions = actionsQuery.data || [];
  const [selectedChoice, setSelectedChoice] = useState<string>('');
  const [clueText, setClueText] = useState('');
  const [clueCount, setClueCount] = useState<number>(1);

  const codenamesHistory = (state as any)?.history || [];
  const codenamesBoard = (state as any)?.board_cards || [];
  const humanPlayer = sessionData?.players?.find((p) => p.human) || sessionData?.players?.[humanPlayerIdx];
  const humanTeam = humanPlayer?.team;
  const humanRole = codenamesRoleFromPlayer(humanPlayer);
  const latestClue = latestClueForTeam(codenamesHistory, humanTeam);
  const codenamesTurnRole = state?.state?.guesses_remaining > 0 ? 'Operatives' : 'Spymaster';
  const codenamesTurnTeam = state?.state?.current_team;
  const isCodenamesTurn = Boolean(game === 'codenames' && humanTeam && humanRole && codenamesTurnTeam && humanTeam === codenamesTurnTeam && humanRole === codenamesTurnRole);
  const isCodenamesOver = isGameOver(state?.state);
  const recentCodenamesActions = [...codenamesHistory].slice(-3).reverse();

  const codenamesPlayAgainMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/games/${game}/sessions`, {
        human_seats: [humanPlayerIdx],
      });
      return res.data;
    },
    onSuccess: (session) => navigate(`/${session.game_slug}/${session.session_id}`),
  });

  if (isLoading || !sessionData) {
    return (
      <div className="container">
        <p>Loading session…</p>
      </div>
    );
  }

  return (
    <div className="container" style={{ display: 'grid', gap: 16 }}>
      <div className="session-topbar">
        <div className="flex" style={{ gap: 8 }}>
          <button className="button secondary" onClick={() => navigate('/')}>🏠 Home</button>
          <button className="button secondary" onClick={() => navigate(`/${game}`)}>← Back</button>
        </div>
        <div className="session-topbar-center">
          {game === 'codenames' ? 'Codenames' : game === 'rps' ? 'Strategic RPS' : sessionData.game_slug}
        </div>
        <span className="badge session-topbar-right">{wsConnected ? 'Live' : 'Offline'}</span>
      </div>

      <div className="card" style={{ display: 'grid', gap: 12 }}>
        <div className="flex" style={{ justifyContent: 'space-between' }}>
          <div className="flex" style={{ gap: 8, alignItems: 'center' }}>
            {isGameOver(state?.state) && (
              <span className="badge" style={{ background: '#dcfce7', color: '#166534' }}>
                {sessionWinnerLabel(state?.state)}
              </span>
            )}
            <span>{isGameOver(state?.state) ? 'Game Over' : `Round ${(state?.state?.current_round ?? 0) + 1}`}</span>
          </div>
        </div>
        {game === 'rps' && state ? (
          <div className="flex" style={{ flexWrap: 'wrap', gap: 16 }}>
            <StatCard
              title="You"
              value={`${state.state?.player1_score ?? 0} pts / ${state.state?.player1_health ?? 0} ♥`}
              highlight={state.state?.game_over && state.state?.winner === 'Player 1'}
            />
            <StatCard
              title={sessionData.players[1]?.name || 'Opponent'}
              value={`${state.state?.player2_score ?? 0} pts / ${state.state?.player2_health ?? 0} ♥`}
              highlight={state.state?.game_over && state.state?.winner === 'Player 2'}
            />
            <StatCard title="Round" value={`${(state.state?.current_round ?? 0) + 1}`} />
          </div>
        ) : game === 'codenames' && state ? (
          <div className="flex" style={{ flexWrap: 'wrap', gap: 16 }}>
            <StatCard title="Red Remaining" value={`${state.state?.red_remaining ?? 0}`} highlight={state.state?.winner === 'Red'} />
            <StatCard title="Blue Remaining" value={`${state.state?.blue_remaining ?? 0}`} highlight={state.state?.winner === 'Blue'} />
            <StatCard
              title="Current Team"
              value={`${state.state?.current_team ?? '—'}`}
              valueColor={state.state?.current_team === 'Red' ? '#dc2626' : state.state?.current_team === 'Blue' ? '#2563eb' : undefined}
            />
            <StatCard title="Guesses Left" value={`${state.state?.guesses_remaining ?? 0}`} />
          </div>
        ) : (
          <p style={{ whiteSpace: 'pre-wrap', fontFamily: 'ui-monospace' }}>{state?.board_view || 'No board view'}</p>
        )}
      </div>

      {game === 'rps' && state?.state?.effect_mapping && action && (
        <div className="card" style={{ display: 'grid', gap: 12 }}>
          <h3>This Round's Effects</h3>
          <div className="flex" style={{ gap: 12, flexWrap: 'wrap' }}>
            {(['rock', 'paper', 'scissors'] as const).map((choice) => {
              const eff = state.state.effect_mapping[choice];
              if (!eff) return null;
              const loseText = eff.lose_type === 'none'
                ? '0'
                : eff.lose_type === 'points'
                ? `-${eff.lose_effect} pts`
                : `-${eff.lose_effect} ♥`;
              const label = choice === 'rock' ? '🪨 Rock' : choice === 'paper' ? '📄 Paper' : '✂️ Scissors';
              return (
                <button
                  key={choice}
                  className="card"
                  style={{
                    minWidth: 160,
                    padding: 12,
                    textAlign: 'left',
                    border: selectedChoice === choice ? '2px solid #22c55e' : '1px solid #e2e8f0',
                    cursor: isTurnOver(state, humanPlayerIdx) ? 'not-allowed' : 'pointer',
                    opacity: isTurnOver(state, humanPlayerIdx) ? 0.6 : 1,
                  }}
                  disabled={isTurnOver(state, humanPlayerIdx)}
                  onClick={() => setSelectedChoice(choice)}
                  type="button"
                >
                  <div style={{ fontWeight: 700 }}>{label}</div>
                  <div style={{ color: '#16a34a' }}>Win: +{eff.win_points} pts</div>
                  <div style={{ color: eff.lose_type === 'none' ? '#16a34a' : eff.lose_type === 'points' ? '#d97706' : '#dc2626' }}>
                    Lose: {loseText}
                  </div>
                </button>
              );
            })}
          </div>
          <div>
            {!state?.state?.game_over ? (
              <button
                className="button"
                style={{ marginTop: 12, opacity: actionMutation.isPending ? 0.7 : 1 }}
                disabled={!selectedChoice || actionMutation.isPending || isTurnOver(state, humanPlayerIdx)}
                onClick={() =>
                  actionMutation.mutate({ action: action.name, params: { choice: selectedChoice } })
                }
              >
                {actionMutation.isPending ? 'Sending…' : 'Submit'}
              </button>
            ) : (
              <div className="flex" style={{ gap: 8, marginTop: 8 }}>
                <button
                  className="button"
                  onClick={() => playAgainMutation.mutate()}
                  disabled={playAgainMutation.isPending}
                >
                  {playAgainMutation.isPending ? 'Starting…' : 'Play Again'}
                </button>
                <button className="button secondary" onClick={() => navigate('/rps')}>
                  Change Opponent
                </button>
              </div>
            )}
          </div>
          {actionMutation.error && <p style={{ color: 'crimson' }}>Error: {(actionMutation.error as any).response?.data?.detail || 'Failed'}</p>}
        </div>
      )}

      {game === 'rps' && state?.state && state.state.last_player1_choice && state.state.last_player2_choice && (
        <div className="card">
          <h3>Last Round</h3>
          <div className="flex" style={{ gap: 12, alignItems: 'center' }}>
            <div>
              You: <strong>{state.state.last_player1_choice}</strong>{' '}
              <span style={{ color: '#475569' }}>{formatOutcome(state.state.last_player1_choice, computeWinner(state.state.last_player1_choice, state.state.last_player2_choice) === 'Player 1', state.state.last_effect_mapping)}</span>
            </div>
            <div>
              {sessionData.players[1]?.name || 'Opponent'}:{' '}
              <strong>{state.state.last_player2_choice}</strong>{' '}
              <span style={{ color: '#475569' }}>{formatOutcome(state.state.last_player2_choice, computeWinner(state.state.last_player1_choice, state.state.last_player2_choice) === 'Player 2', state.state.last_effect_mapping)}</span>
            </div>
            <div style={{ fontWeight: 700, color: computeWinner(state.state.last_player1_choice, state.state.last_player2_choice) === 'Player 1' ? '#16a34a' : computeWinner(state.state.last_player1_choice, state.state.last_player2_choice) === 'Player 2' ? '#16a34a' : '#475569' }}>
              {(() => {
                const w = computeWinner(state.state.last_player1_choice, state.state.last_player2_choice);
                if (w === 'Player 1') return 'You win';
                if (w === 'Player 2') return `${sessionData.players[1]?.name || 'Opponent'} wins`;
                return 'Tie';
              })()}
            </div>
          </div>
        </div>
      )}

      {game === 'codenames' && state && (
        <>
          <div className="card" style={{ display: 'grid', gap: 10 }}>
            <div className="codenames-board-header">
              <h3 className="codenames-board-title">Board</h3>
              <div className="codenames-board-recent">
                {recentCodenamesActions.length > 0 ? (
                  [...recentCodenamesActions].reverse().map((entry: any, idx: number) => (
                    <div key={`${entry.round}-board-${idx}`}>{formatCodenamesHistoryEntry(entry)}</div>
                  ))
                ) : (
                  <div>Recent actions: —</div>
                )}
              </div>
              <div className="codenames-board-clue">
                {!isCodenamesOver && !isCodenamesTurn ? (
                  <>Waiting for {codenamesTurnTeam} {codenamesTurnRole}…</>
                ) : (
                  isCodenamesTurn && (
                    latestClue ? (
                      <>Latest clue: <strong>{latestClue.clue}</strong> ({latestClue.count})</>
                    ) : (
                      <>Latest clue: —</>
                    )
                  )
                )}
              </div>
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
                gap: 8,
              }}
            >
              {codenamesBoard.map((card: any) => {
                const guessAction = actions.find((a) => a.name === 'guess');
                const guessOptions = guessAction?.schema?.properties?.codename?.enum || [];
                const isSelectable = isCodenamesTurn && !isCodenamesOver && guessOptions.includes(card.code);
                const isSelected = selectedChoice === card.code;
                const typeColors: Record<string, string> = {
                  Red: '#fecaca',
                  Blue: '#bfdbfe',
                  Civilian: '#fde68a',
                  Assassin: '#e9d5ff',
                };
                const typeText: Record<string, string> = {
                  Red: '#dc2626',
                  Blue: '#2563eb',
                  Civilian: '#ca8a04',
                  Assassin: '#7c3aed',
                };
                const isRevealed = card.state === 'Revealed';
                const isOperatives = humanRole === 'Operatives';
                const hasType = Boolean(card.type) && (isRevealed || humanRole === 'Spymaster' || (isCodenamesOver && isOperatives));
                const bg = isRevealed ? (card.type ? typeColors[card.type] : '#f8fafc') : '#ffffff';
                const color = hasType ? typeText[card.type || 'Civilian'] : '#0f172a';
                const isDimmed = !isSelectable && humanRole !== 'Spymaster';
                return (
                  <button
                    key={card.id}
                    type="button"
                    onClick={() => isSelectable && setSelectedChoice(card.code)}
                    className="card"
                    style={{
                      padding: '12px 8px',
                      minHeight: 56,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: 0.5,
                      background: bg,
                      color,
                      textShadow: 'none',
                      border: isSelected ? '2px solid #22c55e' : '1px solid #e2e8f0',
                      opacity: isSelected || !isDimmed ? 1 : 0.6,
                      cursor: isSelectable ? 'pointer' : 'default',
                    }}
                    disabled={!isSelectable}
                    title={card.type ? `${card.type} ${card.state}` : card.state}
                  >
                    {card.code}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="card" style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box', display: 'grid', gap: 10 }}>
            {actions.find((a) => a.name === 'clue') && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const clueAction = actions.find((a) => a.name === 'clue');
                  if (!clueAction) return;
                  actionMutation.mutate({ action: clueAction.name, params: { clue: clueText, count: clueCount } });
                }}
                style={{ display: 'grid', gap: 8 }}
              >
                <label style={{ display: 'grid', gap: 6 }}>
                  Clue word
                  <input
                    type="text"
                    value={clueText}
                    onChange={(e) => setClueText(e.target.value)}
                    required
                    placeholder="One word"
                    disabled={!isCodenamesTurn || isCodenamesOver}
                  />
                </label>
                <label style={{ display: 'grid', gap: 6 }}>
                  Number of cards
                  <input
                    type="number"
                    min={1}
                    max={9}
                    value={clueCount}
                    onChange={(e) => setClueCount(Number(e.target.value))}
                    required
                    disabled={!isCodenamesTurn || isCodenamesOver}
                  />
                </label>
                {isCodenamesOver ? (
                  <div style={{ display: 'flex', gap: 10, width: '100%' }}>
                    <button
                      className="button"
                      onClick={() => codenamesPlayAgainMutation.mutate()}
                      disabled={codenamesPlayAgainMutation.isPending}
                      style={{ flex: 1 }}
                      type="button"
                    >
                      {codenamesPlayAgainMutation.isPending ? 'Starting…' : 'Play Again'}
                    </button>
                    <button
                      className="button secondary"
                      onClick={() => navigate('/codenames')}
                      style={{ flex: 1 }}
                      type="button"
                    >
                      Settings
                    </button>
                  </div>
                ) : (
                  <button className="button" type="submit" disabled={actionMutation.isPending || !clueText || !isCodenamesTurn || isCodenamesOver}>
                    {actionMutation.isPending ? 'Sending…' : 'Submit Clue'}
                  </button>
                )}
              </form>
            )}
            {(actions.find((a) => a.name === 'guess') || actions.find((a) => a.name === 'pass')) && (
              <div style={{ display: 'flex', gap: 10, width: '100%' }}>
                {isCodenamesOver ? (
                  <>
                    <button
                      className="button"
                      onClick={() => codenamesPlayAgainMutation.mutate()}
                      disabled={codenamesPlayAgainMutation.isPending}
                      style={{ flex: 1 }}
                    >
                      {codenamesPlayAgainMutation.isPending ? 'Starting…' : 'Play Again'}
                    </button>
                    <button
                      className="button secondary"
                      onClick={() => navigate('/codenames')}
                      style={{ flex: 1 }}
                    >
                      Settings
                    </button>
                  </>
                ) : (
                  <>
                    {actions.find((a) => a.name === 'guess') && (
                      <button
                        className="button"
                        onClick={() => {
                          const guessAction = actions.find((a) => a.name === 'guess');
                          if (!guessAction) return;
                          actionMutation.mutate({ action: guessAction.name, params: { codename: selectedChoice } });
                        }}
                        disabled={actionMutation.isPending || !selectedChoice || !isCodenamesTurn || isCodenamesOver}
                        style={{ flex: 1 }}
                      >
                        {actionMutation.isPending ? 'Sending…' : 'Submit'}
                      </button>
                    )}
                    {actions.find((a) => a.name === 'pass') && (
                      <button
                        className="button secondary"
                        onClick={() => actionMutation.mutate({ action: 'pass', params: {} })}
                        disabled={actionMutation.isPending || !isCodenamesTurn || isCodenamesOver}
                        style={{ flex: 1 }}
                      >
                        Pass
                      </button>
                    )}
                  </>
                )}
              </div>
            )}
            {actionMutation.error && <p style={{ color: 'crimson' }}>Error: {(actionMutation.error as any).response?.data?.detail || 'Failed'}</p>}
          </div>


          <div className="card" style={{ display: 'grid', gap: 8 }}>
            <h3>Action History</h3>
            {codenamesHistory.length === 0 ? (
              <div style={{ color: '#475569' }}>No actions yet.</div>
            ) : (
              <div
                style={{
                  maxHeight: 160,
                  overflowY: 'auto',
                }}
              >
                {[...codenamesHistory].reverse().map((entry: any, idx: number) => (
                  <div key={`${entry.round}-${idx}`} style={{ fontSize: 14, marginBottom: 6, lineHeight: '20px' }}>
                    {formatCodenamesHistoryEntry(entry)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
