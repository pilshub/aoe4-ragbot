"use client";

import { useLang } from "../lib/LangContext";

const PATTERNS: Array<{ match: RegExp; key: string }> = [
  { match: /Vortix|guía de|guide|edad|age|landmark|composición|composition|feudal|castle|imperial|### [IV]+\s*—|Matchups|Valoración/i, key: "strategy" },
  { match: /win\s*rate|pick\s*rate|statistics|winrate|porcentaje|estadístic/i, key: "winrate" },
  { match: /build\s*order|strategy|guide|opening|estrategia|guía|apertura/i, key: "buildOrder" },
  { match: /unit|damage|armor|hitpoints|hp\b|unidad|daño|armadura/i, key: "unit" },
  { match: /counter|weak|strong against|beats|contrar|débil|fuerte contra|matchup/i, key: "counter" },
  { match: /leaderboard|rank|top player|elo\b|ranking|mejor jugador/i, key: "leaderboard" },
  { match: /patch|season|update|nerf|buff|temporada|parche/i, key: "patch" },
];

interface Props {
  messageContent: string;
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({ messageContent, onSelect }: Props) {
  const { t } = useLang();
  const suggestions: string[] = [];

  for (const p of PATTERNS) {
    if (p.match.test(messageContent)) {
      const group = t.suggestions[p.key as keyof typeof t.suggestions];
      if (group) {
        for (const s of group) {
          if (!suggestions.includes(s)) suggestions.push(s);
        }
      }
      if (suggestions.length >= 3) break;
    }
  }

  if (suggestions.length === 0) return null;

  return (
    <div className="mt-3 pt-2.5 pb-1 px-3 -mx-1 rounded-md border-t border-border bg-[rgba(201,168,76,0.04)]">
      <p className="text-xs text-text-dim mb-1.5 font-[family-name:var(--font-heading)] uppercase tracking-wider">
        {t.relatedQuestions}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.slice(0, 3).map((q, i) => (
          <button
            key={i}
            onClick={() => onSelect(q)}
            className="text-xs px-2.5 py-1 rounded border border-border text-text-secondary
                       hover:border-border-gold hover:text-gold transition-all cursor-pointer
                       font-[family-name:var(--font-body)]"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
