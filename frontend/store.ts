import { MODERATORS, SEED_QUEUE, SEVERITY_RANK, assignModerator, type Moderator, type QueueItem } from "./moderation";

export type StoredItem = QueueItem & {
  seq: number;
  assignedTo: string | null;
  submittedBy: string | null;
  reason: string;
  action?: string;
};
export type AppState = { loads: Record<string, number>; items: StoredItem[]; seq: number };

const KEY = "tns-state-v1";

/** Moderators with their live workload. */
export function liveMods(state: AppState): Moderator[] {
  return MODERATORS.map((m) => ({ ...m, assigned: state.loads[m.id] ?? m.assigned }));
}

function route(state: AppState, item: QueueItem, submittedBy: string | null): StoredItem {
  const a = assignModerator(item.language, item.severity, liveMods(state));
  if (a.moderator) state.loads[a.moderator.id] = (state.loads[a.moderator.id] ?? a.moderator.assigned) + 1;
  state.seq += 1;
  return { ...item, seq: state.seq, assignedTo: a.moderator?.id ?? null, submittedBy, reason: a.reason };
}

function initial(): AppState {
  const s: AppState = { loads: Object.fromEntries(MODERATORS.map((m) => [m.id, m.assigned])), items: [], seq: 0 };
  for (const it of SEED_QUEUE) s.items.push(route(s, it, null));
  return s;
}

export function loadState(): AppState {
  const raw = localStorage.getItem(KEY);
  if (raw) return JSON.parse(raw) as AppState;
  const s = initial();
  saveState(s);
  return s;
}
const saveState = (s: AppState) => localStorage.setItem(KEY, JSON.stringify(s));

export function submitComment(item: QueueItem, userId: string): StoredItem {
  const s = loadState();
  const stored = route(s, item, userId);
  s.items.push(stored);
  saveState(s);
  return stored;
}

/** Moderator resolves an item: frees capacity, then pulls buffered items (Severe → Moderate → Mild, then arrival). */
export function resolveItem(postId: string, action: string): AppState {
  const s = loadState();
  const it = s.items.find((x) => x.postId === postId);
  if (!it || it.action) return s;
  it.action = action;
  if (it.assignedTo) s.loads[it.assignedTo] = Math.max(0, (s.loads[it.assignedTo] ?? 1) - 1);
  const buffered = s.items
    .filter((x) => !x.assignedTo && !x.action)
    .sort((a, b) => SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity] || a.seq - b.seq);
  for (const b of buffered) {
    const a = assignModerator(b.language, b.severity, liveMods(s));
    if (a.moderator) {
      b.assignedTo = a.moderator.id;
      b.reason = a.reason;
      s.loads[a.moderator.id] = (s.loads[a.moderator.id] ?? 0) + 1;
    }
  }
  saveState(s);
  return s;
}
