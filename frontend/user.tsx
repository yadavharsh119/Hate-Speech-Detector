import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { classify, clearSession, loadSession, type AppUser, type Severity } from "@/lib/moderation";
import { loadState, submitComment, type StoredItem } from "@/lib/store";

export const Route = createFileRoute("/user")({
  head: () => ({
    meta: [
      { title: "Post a Comment — Trust & Safety Portal" },
      { name: "description", content: "Submit comments in English, Hindi or Marathi for moderation." },
      { property: "og:title", content: "Post a Comment — Trust & Safety Portal" },
      { property: "og:description", content: "Submit comments in English, Hindi or Marathi for moderation." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: UserPage,
});

const badgeClass: Record<Severity, string> = {
  "Severe Hate": "badge-severe",
  "Moderate Hate": "badge-moderate",
  "Mild Hate": "badge-mild",
};


function UserPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<AppUser | null>(null);
  const [text, setText] = useState("");
  const [mine, setMine] = useState<StoredItem[]>([]);

  const refresh = (u: AppUser) => setMine(loadState().items.filter((x) => x.submittedBy === u.id).reverse());

  useEffect(() => {
    const s = loadSession();
    if (!s || s.kind !== "user") return void navigate({ to: "/", replace: true });
    const u = s.user;
    setUser(u);
    refresh(u);
    const r = () => refresh(u);
    window.addEventListener("storage", r);
    window.addEventListener("focus", r);
    return () => { window.removeEventListener("storage", r); window.removeEventListener("focus", r); };
  }, [navigate]);

  if (!user) return null;

  const submit = () => {
    if (!text.trim()) return;
    submitComment(
      {
        postId: `POST_${Date.now().toString().slice(-6)}`,
        timestamp: new Date().toISOString().slice(0, 16).replace("T", " "),
        text: text.trim(),
        ...classify(text),
      },
      user.id,
    );
    setText("");
    refresh(user);
  };

  return (
    <main className="mx-auto max-w-3xl p-6 md:p-10">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-bold">🛡️ Trust & Safety</p>
          <h1 className="text-2xl font-bold">Welcome, {user.name}</h1>
          <p className="font-mono text-xs text-primary">{user.id}</p>
        </div>
        <button
          onClick={() => { clearSession(); navigate({ to: "/", replace: true }); }}
          className="rounded-md border px-3 py-2 text-sm text-muted-foreground transition hover:border-destructive hover:text-destructive"
        >
          Logout
        </button>
      </div>

      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
        className="mt-8 w-full rounded-lg border border-input bg-card p-4 text-base outline-none focus:border-primary"
        placeholder="Write a comment in English, Hindi or Marathi…" />
      <button onClick={submit} className="mt-3 rounded-md bg-primary px-5 py-2 font-semibold text-primary-foreground transition hover:opacity-90">
        Post Comment
      </button>

      <h2 className="mt-10 text-lg font-semibold">My comments</h2>
      <div className="mt-3 space-y-3">
        {mine.length === 0 && <p className="text-sm text-muted-foreground">No comments yet.</p>}
        {mine.map((c) => (
          <article key={c.postId} className="rounded-xl border bg-card p-4">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-mono">{c.postId}</span>
              <span className="text-muted-foreground">{c.timestamp}</span>
              <span className="rounded bg-secondary px-2 py-0.5">{c.language}</span>
              <span className={`${badgeClass[c.severity]} rounded-full px-2.5 py-0.5 font-semibold`}>{c.severity}</span>
              <span className="ml-auto font-mono">AI {c.confidence}%</span>
            </div>
            <p className="mt-2">{c.text}</p>
            {!c.action && <p className="mt-2 text-sm text-muted-foreground">⏳ Under review</p>}
            {c.action && (
              <p className={`mt-3 rounded-md px-3 py-2 text-sm font-medium ${c.action.startsWith("Deleted") ? "badge-severe" : c.action.startsWith("Warning") ? "badge-mild" : "border text-safe"}`}>
                {c.action.startsWith("Deleted") ? "🔴 Your comment has been deleted and a strike has been issued." : c.action.startsWith("Warning") ? "🟡 Warning received for your comment." : "🟢 Your comment has been marked safe."}
              </p>
            )}
          </article>
        ))}
      </div>
    </main>
  );
}
