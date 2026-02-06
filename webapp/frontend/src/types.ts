export type GameMeta = {
  slug: string;
  title: string;
  description: string;
  min_players: number;
  max_players: number;
  playable: boolean;
  tags?: string[];
};

export type SessionState = {
  session_id: string;
  game_slug: string;
  players: Array<{ idx: number; team?: string; name?: string; human?: boolean }>;
  config?: Record<string, any>;
  state: Record<string, any>;
  board_view?: string | null;
  board_cards?: Array<{ id: number; code: string; state: string; type?: string | null }>;
  history?: Array<Record<string, any>>;
  turn?: number | null;
};

export type ActionSchema = {
  name: string;
  display_name: string;
  schema?: any;
};

export type SessionEvent =
  | { type: 'session_state'; state: any; turn?: number }
  | { type: 'action_applied'; turn: number; action: string; params: any; state: any }
  | { type: 'game_over'; state: any }
  | { type: 'error'; message: string };
