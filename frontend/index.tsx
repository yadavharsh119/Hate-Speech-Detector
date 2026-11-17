import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { MODERATORS, USERS, authenticate, saveSession } from "@/lib/moderation";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Moderator Login — Trust & Safety Portal" },
      { name: "description", content: "Sign in to the multilingual hate speech moderation portal." },
      { property: "og:title", content: "Moderator Login — Trust & Safety Portal" },
      { property: "og:description", content: "Sign in to the multilingual hate speech moderation portal." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Login,
});

function Login() {
  const navigate = useNavigate();
  const [id, setId] = useState("");
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const session = authenticate(id, pw);
    if (!session) return setError("Invalid User ID or Password.");
    saveSession(session);
    navigate({ to: session.kind === "mod" ? "/dashboard" : "/user" });
  };

  const input = "w-full rounded-md border border-input bg-background px-3 py-2.5 font-mono text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-ring/30";

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <form onSubmit={submit} className="rounded-xl border bg-card p-8 shadow-glow">
          <h1 className="text-2xl font-bold">🛡️ Trust & Safety Moderator Portal</h1>
          <p className="mt-1 text-sm text-muted-foreground">Multilingual Hate Speech Detection Platform</p>
          <label className="mt-6 block text-xs font-medium uppercase tracking-wider text-muted-foreground">User ID</label>
          <input className={`${input} mt-1.5`} value={id} onChange={(e) => setId(e.target.value)} placeholder="MOD_1" />
          <label className="mt-4 block text-xs font-medium uppercase tracking-wider text-muted-foreground">Password</label>
          <input type="password" className={`${input} mt-1.5`} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="••••••" />
          {error && <p className="mt-3 text-sm text-destructive">{error}</p>}
          <button className="mt-6 w-full rounded-md bg-primary py-2.5 font-semibold text-primary-foreground transition hover:opacity-90">Sign in</button>
        </form>
        <div className="mt-4 rounded-lg border bg-card/60 p-4 font-mono text-xs text-muted-foreground">
          <p className="mb-2 text-foreground">Demo accounts (click to fill)</p>
          {MODERATORS.map((m) => {
            const p = `pass${m.id.split("_")[1]}`;
            return (
              <button key={m.id} type="button" onClick={() => { setId(m.id); setPw(p); }} className="block w-full rounded px-1 py-0.5 text-left hover:bg-accent hover:text-foreground">
                {m.id} / {p} — {m.name} ({m.role})
              </button>
            );
          })}
          <p className="mb-2 mt-3 text-foreground">User accounts</p>
          {USERS.map((u) => {
            const p = `user${u.id.split("_")[1]}`;
            return (
              <button key={u.id} type="button" onClick={() => { setId(u.id); setPw(p); }} className="block w-full rounded px-1 py-0.5 text-left hover:bg-accent hover:text-foreground">
                {u.id} / {p} — {u.name}
              </button>
            );
          })}
        </div>
      </div>
    </main>
  );
}
