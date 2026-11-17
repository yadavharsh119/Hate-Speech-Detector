export type Moderator = {
  id: string;
  name: string;
  languages: string;
  role: string;
  assigned: number;
  max: number;
};

export const MODERATORS: Moderator[] = [
  { id: "MOD_1", name: "Aarav Sharma", role: "Junior", languages: "English, Hindi", assigned: 1, max: 5 },
  { id: "MOD_2", name: "Priya Kulkarni", role: "Senior", languages: "English, Hindi, Marathi", assigned: 3, max: 5 },
  { id: "MOD_3", name: "Rohan Deshmukh", role: "Junior", languages: "Marathi", assigned: 5, max: 5 },
  { id: "MOD_4", name: "Ananya Iyer", role: "Senior", languages: "English", assigned: 0, max: 5 },
  { id: "MOD_5", name: "Vikram Patil", role: "Senior", languages: "Marathi, Hindi", assigned: 4, max: 5 },
  { id: "MOD_6", name: "Neha Verma", role: "Junior", languages: "English, Hindi", assigned: 2, max: 5 },
  { id: "MOD_7", name: "Siddharth Joshi", role: "Junior", languages: "Hindi, Marathi", assigned: 1, max: 5 },
  { id: "MOD_8", name: "Kavita Rao", role: "Senior", languages: "English, Hindi, Marathi", assigned: 5, max: 5 },
];

export type AppUser = { id: string; name: string };
export const USERS: AppUser[] = [
  { id: "USER_1", name: "User 1" },
  { id: "USER_2", name: "User 2" },
  { id: "USER_3", name: "User 3" },
];

export type Session = { kind: "mod"; mod: Moderator } | { kind: "user"; user: AppUser };

/** MOD_n / passn, USER_n / usern. */
export function authenticate(id: string, password: string): Session | null {
  const key = id.trim().toUpperCase();
  const n = key.split("_")[1];
  const mod = MODERATORS.find((m) => m.id === key);
  if (mod) return password === `pass${n}` ? { kind: "mod", mod } : null;
  const user = USERS.find((u) => u.id === key);
  if (user) return password === `user${n}` ? { kind: "user", user } : null;
  return null;
}

export type Assignment = {
  status: "ASSIGNED" | "QUEUED";
  moderator: Moderator | null;
  reason: string;
};

/**
 * CSP router. Hard: language match, active load < max capacity.
 * Priority: Severe → Senior only. Tie-break: lowest workload ratio (first in list on equal ratio).
 */
export function assignModerator(language: Language, severity: Severity, mods: Moderator[] = MODERATORS): Assignment {
  const severe = severity === "Severe Hate";
  const candidates = mods.filter(
    (m) => m.assigned < m.max && REQUIRED_LANGUAGES[language].every((l) => m.languages.split(", ").includes(l)) && (!severe || m.role.toLowerCase() === "senior"),
  );
  if (!candidates.length) {
    return { status: "QUEUED", moderator: null, reason: `No available moderator found for language '${language}' with severity '${severity}' and active capacity.` };
  }
  const m = candidates.reduce((best, c) => (c.assigned / c.max < best.assigned / best.max ? c : best));
  const pct = Math.round((m.assigned / m.max) * 1000) / 10;
  return {
    status: "ASSIGNED",
    moderator: m,
    reason: `Matched language '${language}'; ${severe ? "Enforced Senior role due to Severe rating; " : ""}Selected ${m.name} with lowest workload ratio (${pct}% capacity used).`,
  };
}

const KEY = "tns-session";
export const saveSession = (s: Session) => sessionStorage.setItem(KEY, JSON.stringify(s));
export const loadSession = (): Session | null => {
  const raw = sessionStorage.getItem(KEY);
  return raw ? (JSON.parse(raw) as Session) : null;
};
export const clearSession = () => sessionStorage.removeItem(KEY);

export type Severity = "Severe Hate" | "Moderate Hate" | "Mild Hate";
export type Language = "English" | "Hindi" | "Marathi" | "Hinglish" | "Marathi-English";

/** Languages a moderator must know to handle a comment. Mixed (Roman-script) comments need both. */
export const REQUIRED_LANGUAGES: Record<Language, string[]> = {
  English: ["English"],
  Hindi: ["Hindi"],
  Marathi: ["Marathi"],
  Hinglish: ["Hindi", "English"],
  "Marathi-English": ["Marathi", "English"],
};

export type QueueItem = {
  postId: string;
  timestamp: string;
  text: string;
  language: Language;
  severity: Severity;
  confidence: number;
};

export const SEVERITY_RANK: Record<Severity, number> = { "Severe Hate": 3, "Moderate Hate": 2, "Mild Hate": 1 };

/** Max-priority queue: higher severity first, then higher confidence. */
export class PriorityQueue {
  private heap: QueueItem[] = [];
  private static higher(a: QueueItem, b: QueueItem) {
    const d = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];
    return d !== 0 ? d > 0 : a.confidence > b.confidence;
  }
  push(item: QueueItem) {
    const h = this.heap;
    h.push(item);
    let i = h.length - 1;
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (!PriorityQueue.higher(h[i]!, h[p]!)) break;
      const t = h[i]!; h[i] = h[p]!; h[p] = t;
      i = p;
    }
  }
  pop(): QueueItem | undefined {
    const h = this.heap;
    if (!h.length) return undefined;
    const top = h[0];
    const last = h.pop()!;
    if (h.length) {
      h[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < h.length && PriorityQueue.higher(h[l]!, h[m]!)) m = l;
        if (r < h.length && PriorityQueue.higher(h[r]!, h[m]!)) m = r;
        if (m === i) break;
        const t = h[i]!; h[i] = h[m]!; h[m] = t;
        i = m;
      }
    }
    return top;
  }
}

export function sortByPriority(items: QueueItem[]): QueueItem[] {
  const pq = new PriorityQueue();
  items.forEach((i) => pq.push(i));
  const out: QueueItem[] = [];
  let x;
  while ((x = pq.pop())) out.push(x);
  return out;
}

export const SEED_QUEUE: QueueItem[] = [
  { postId: "POST_4821", timestamp: "2026-10-11 09:14", text: "तुम लोग यहाँ से चले जाओ वरना परिणाम बुरा होगा!", language: "Hindi", severity: "Severe Hate", confidence: 96 },
  { postId: "POST_4822", timestamp: "2026-10-11 09:21", text: "तुमचा हा मूर्खपणा आता सहन केला जाणार नाही!", language: "Marathi", severity: "Moderate Hate", confidence: 88 },
  { postId: "POST_4823", timestamp: "2026-10-11 09:33", text: "People like you should be kicked out of this country.", language: "English", severity: "Severe Hate", confidence: 91 },
  { postId: "POST_4824", timestamp: "2026-10-11 09:40", text: "What a stupid take, honestly. Go back to school.", language: "English", severity: "Mild Hate", confidence: 72 },
  { postId: "POST_4825", timestamp: "2026-10-11 09:52", text: "ये लोग बेवकूफ हैं, इनकी बात मत सुनो।", language: "Hindi", severity: "Moderate Hate", confidence: 83 },
  { postId: "POST_4826", timestamp: "2026-10-11 10:05", text: "तू खूप वेडा आहेस रे.", language: "Marathi", severity: "Mild Hate", confidence: 65 },
];

const SEVERE = ["kill", "destroy", "kicked out", "get out", "eliminate", "चले जाओ", "परिणाम बुरा", "मार", "खत्म", "हाकलून", "ठार", "जीव घेऊ"];
const MODERATE = ["hate", "disgusting", "idiot", "trash", "बेवकूफ", "नफरत", "गंदे", "मूर्खपणा", "सहन", "घाणेरडा", "नालायक"];
const MILD = ["stupid", "dumb", "loser", "shut up", "pagal", "पागल", "बकवास", "वेडा", "मूर्ख", "फालतू"];

const ROMAN_MARATHI = ["ahe", "aahe", "ahes", "nahiye", "tumcha", "tumchi", "majha", "maza", "tula", "mala", "kay", "kasa", "kashi", "ata", "aata", "jaanar", "jaa", "re", "khup", "vedya", "veda", "kela", "keli", "hota", "bagh", "ani"];
const ROMAN_HINDI = ["hai", "hain", "ho", "tum", "tu", "tujhe", "mujhe", "kya", "kyu", "kyun", "nahi", "nahin", "yaha", "yahan", "wahan", "chale", "jao", "bhai", "log", "mat", "kar", "karo", "bahut", "pagal", "bewakoof", "warna", "abhi", "mera", "tera"];

export function detectLanguage(text: string): Language {
  if (!/[\u0900-\u097F]/.test(text)) {
    const words = text.toLowerCase().split(/[^a-z]+/);
    const has = (list: string[]) => list.some((w) => words.includes(w));
    if (has(ROMAN_MARATHI)) return "Marathi-English";
    if (has(ROMAN_HINDI)) return "Hinglish";
    return "English";
  }
  const marathi = ["आहे", "आहेस", "तुमचा", "तू ", "नाही", "केला", "जाणार", "रे"];
  return marathi.some((w) => text.includes(w)) ? "Marathi" : "Hindi";
}

export function classify(text: string): { severity: Severity; confidence: number; language: Language } {
  const t = text.toLowerCase();
  const hits = (list: string[]) => list.filter((k) => t.includes(k.toLowerCase())).length;
  const s = hits(SEVERE), m = hits(MODERATE), l = hits(MILD);
  const language = detectLanguage(text);
  if (s) return { severity: "Severe Hate", confidence: Math.min(99, 88 + s * 4), language };
  if (m) return { severity: "Moderate Hate", confidence: Math.min(95, 76 + m * 5), language };
  return { severity: "Mild Hate", confidence: l ? Math.min(85, 64 + l * 6) : 52, language };
}
