"use client";

const EXAMPLES = [
  { text: "What's the best counter to French Knights?", icon: "⚔" },
  { text: "Show me English Fast Castle build orders", icon: "🏰" },
  { text: "Who is #1 on the ranked leaderboard?", icon: "👑" },
  { text: "Compare Longbowman vs Archer stats", icon: "🏹" },
  { text: "What is the current win rate of Mongols?", icon: "📊" },
  { text: "Tell me about the Ottoman civilization", icon: "✦" },
];

interface Props {
  onSelect: (question: string) => void;
}

export default function WelcomeScreen({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-4 py-16">
      {/* Logo */}
      <div className="w-24 h-24 rounded-lg card-medieval flex items-center justify-center mb-6 shadow-gold border-border-gold">
        <span className="text-gold font-[family-name:var(--font-heading)] font-black text-4xl">
          IV
        </span>
      </div>

      <h2 className="text-gold font-[family-name:var(--font-heading)] font-bold text-3xl mb-2 text-center tracking-wide">
        AoE4 Bot
      </h2>
      <div className="ornament-line w-48 my-3" />
      <p className="text-text-secondary text-base mb-10 text-center max-w-lg font-[family-name:var(--font-body)]">
        Ask me anything about Age of Empires IV — civilizations, strategies, unit stats,
        build orders, pro players, win rates, and more.
      </p>

      {/* Example questions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
        {EXAMPLES.map((q) => (
          <button
            key={q.text}
            onClick={() => onSelect(q.text)}
            className="text-left px-4 py-3 rounded-lg card-medieval
                       text-text-primary text-sm
                       hover:border-border-gold hover:bg-bg-card-hover
                       transition-all cursor-pointer flex items-start gap-3"
          >
            <span className="text-lg mt-0.5">{q.icon}</span>
            <span className="font-[family-name:var(--font-body)]">{q.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
