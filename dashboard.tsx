import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { clearSession, loadSession, sortByPriority, type Moderator, type Severity } from "@/lib/moderation";
import { liveMods, loadState, resolveItem, type AppState, type StoredItem } from "@/lib/store";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Moderation Dashboard — Trust & Safety Portal" },
      { name: "description", content: "Priority queue of flagged multilingual comments for review." },
      { property: "og:title", content: "Moderation Dashboard — Trust & Safety Portal" },
      { property: "og:description", content: "Priority queue of flagged multilingual comments for review." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: Dashboard,
});

const badgeClass: Record<Severity, string> = {
  "Severe Hate": "badge-severe",
  "Moderate Hate": "badge-moderate",
  "Mild Hate": "badge-mild",
};

export function SeverityBadge({ s }: { s: Severity }) {
  return <span className={`${badgeClass[s]} rounded-full px-2.5 py-0.5 text-xs font-semibold`}>{s}</span>;
}

function Dashboard() {
  const navigate = useNavigate();
  const [modId, setModId] = useState<string | null>(null);
  const [state, setState] = useState<AppState | null>(null);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const s = loadSession();
    if (!s || s.kind !== "mod") return void navigate({ to: "/", replace: true });
    setModId(s.mod.id);
    setState(loadState());
    const refresh = () => setState(loadState());
    window.addEventListener("storage", refresh);
    window.addEventListener("focus", refresh);
    return () => {
      window.removeEventListener("storage", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, [navigate]);

  const mod: Moderator | undefined = state ? liveMods(state).find((m) => m.id === modId) : undefined;
  const queue = useMemo(
    () => (state && modId ? (sortByPriority(state.items.filter((x) => x.assignedTo === modId && !x.action)) as StoredItem[]) : []),
    [state, modId],
  );

  const act = (id: string, label: string) => {
    setState(resolveItem(id, label));
    setToast(`${id}: ${label}`);
    setTimeout(() => setToast(""), 2500);
  };

  const logout = () => {
    clearSession();
    navigate({ to: "/", replace: true });
  };

  if (!mod) return null;
  const pct = (mod.assigned / mod.max) * 100;

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="border-b bg-card p-6 md:w-72 md:border-b-0 md:border-r">
        <p className="text-sm font-bold">🛡️ Trust & Safety</p>
        <div className="mt-6 rounded-lg border bg-background p-4">
          <p className="text-lg font-semibold">{mod.name}</p>
          <p className="font-mono text-xs text-primary">{mod.id}</p>
          <p className="mt-2 text-sm text-muted-foreground">{mod.role}</p>
          <p className="mt-3 text-xs uppercase tracking-wider text-muted-foreground">Languages</p>
          <div className="mt-1 flex flex-wrap gap-1">
            {mod.languages.split(", ").map((l) => (
              <span key={l} className="rounded bg-secondary px-2 py-0.5 text-xs">{l}</span>
            ))}
          </div>
        </div>
        <div className="mt-4">
          <p className="text-xs text-muted-foreground">CSP Capacity</p>
          <p className="text-sm font-medium">Assigned Workload: {mod.assigned}/{mod.max} Max Capacity</p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
          </div>
        </div>
        <button onClick={logout} className="mt-6 w-full rounded-md border px-3 py-2 text-sm text-muted-foreground transition hover:border-destructive hover:text-destructive">
          Logout
        </button>
      </aside>

      <main className="flex-1 p-6 md:p-10">
        <h1 className="text-2xl font-bold">Priority Queue Feed</h1>
        <p className="text-sm text-muted-foreground">Comments assigned to you, sorted by severity, then AI confidence.</p>
        <div className="mt-6 space-y-4">
          {queue.length === 0 && <p className="text-muted-foreground">Queue is clear. 🎉</p>}
          {queue.map((q, i) => (
            <article key={q.postId} className="rounded-xl border bg-card p-5 transition hover:shadow-glow animate-in fade-in slide-in-from-bottom-2">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-mono text-primary">#{i + 1}</span>
                <span className="font-mono">{q.postId}</span>
                <span className="text-muted-foreground">{q.timestamp}</span>
                <span className="rounded bg-secondary px-2 py-0.5">{q.language}</span>
                <SeverityBadge s={q.severity} />
                {q.submittedBy && <span className="text-muted-foreground">from {q.submittedBy}</span>}
                <span className="ml-auto font-mono text-sm">AI {q.confidence}%</span>
              </div>
              <p className="mt-3 text-lg leading-relaxed" lang={q.language === "Hindi" ? "hi" : q.language === "Marathi" ? "mr" : "en"}>{q.text}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-sm">
                <button onClick={() => act(q.postId, "Deleted & strike issued")} className="badge-severe rounded-md px-3 py-1.5 transition hover:opacity-80">🔴 Delete & Issue Strike</button>
                <button onClick={() => act(q.postId, "Warning sent")} className="badge-mild rounded-md px-3 py-1.5 transition hover:opacity-80">🟡 Send Warning</button>
                <button onClick={() => act(q.postId, "Marked safe")} className="rounded-md border px-3 py-1.5 text-safe transition hover:opacity-80">🟢 Mark Safe / Dismiss</button>
              </div>
            </article>
          ))}
        </div>
      </main>
      {toast && <div className="fixed bottom-6 right-6 rounded-lg border bg-card px-4 py-3 text-sm shadow-glow">{toast}</div>}
    </div>
  );
}
