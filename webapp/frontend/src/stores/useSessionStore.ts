import { create } from 'zustand';
import { SessionEvent, SessionState } from '../types';

interface SessionStore {
  state: SessionState | null;
  events: SessionEvent[];
  setState: (s: SessionState) => void;
  pushEvent: (ev: SessionEvent) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  state: null,
  events: [],
  setState: (s) => set({ state: s }),
  pushEvent: (ev) =>
    set((prev) => ({
      events: [...prev.events.slice(-50), ev],
      state:
        ev.type === 'session_state'
          ? { ...(prev.state || {}), ...ev.state, turn: ev.turn ?? (prev.state as any)?.turn }
          : ev.type === 'action_applied'
          ? { ...(prev.state || {}), ...ev.state, turn: ev.turn }
          : ev.type === 'game_over'
          ? { ...(prev.state || {}), ...ev.state }
          : prev.state,
    })),
  reset: () => set({ state: null, events: [] }),
}));
