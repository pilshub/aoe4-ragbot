"use client";

const PATTERNS: Array<{ match: RegExp; suggestions: string[] }> = [
  {
    match: /win\s*rate|pick\s*rate|statistics|winrate/i,
    suggestions: [
      "Show me the matchups against the top civs",
      "What are the best build orders for this civ?",
      "How does this compare in team games?",
    ],
  },
  {
    match: /build\s*order|strategy|guide|opening/i,
    suggestions: [
      "What are the key timings for this build?",
      "What counters this strategy?",
      "Any pro player tips for this approach?",
    ],
  },
  {
    match: /unit|damage|armor|hitpoints|hp\b/i,
    suggestions: [
      "What counters this unit?",
      "Compare this with similar units",
      "What upgrades improve this unit?",
    ],
  },
  {
    match: /counter|weak|strong against|beats/i,
    suggestions: [
      "Show me a build order for this matchup",
      "What do pro players recommend?",
      "What's the win rate in this matchup?",
    ],
  },
  {
    match: /leaderboard|rank|top player|elo\b/i,
    suggestions: [
      "What civilization does the #1 player main?",
      "Show me the esports tournament rankings",
      "Who are the top players from Spain?",
    ],
  },
  {
    match: /patch|season|update|nerf|buff/i,
    suggestions: [
      "Which civs are strongest this season?",
      "Show me the current tier list",
      "What changed for my main civ?",
    ],
  },
];

interface Props {
  messageContent: string;
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({ messageContent, onSelect }: Props) {
  const suggestions: string[] = [];
  for (const p of PATTERNS) {
    if (p.match.test(messageContent)) {
      for (const s of p.suggestions) {
        if (!suggestions.includes(s)) suggestions.push(s);
      }
      if (suggestions.length >= 3) break;
    }
  }

  if (suggestions.length === 0) return null;

  return (
    <div className="mt-3 pt-2 border-t border-border">
      <p className="text-xs text-text-dim mb-1.5 font-[family-name:var(--font-heading)] uppercase tracking-wider">
        Related Questions
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
