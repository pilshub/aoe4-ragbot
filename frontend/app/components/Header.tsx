"use client";

interface Props {
  onLogoClick?: () => void;
}

export default function Header({ onLogoClick }: Props) {
  return (
    <header className="border-b border-border bg-bg-dark/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
        {/* Shield icon — clickable to return to welcome screen */}
        <button
          onClick={onLogoClick}
          className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
        >
          <div className="w-10 h-10 rounded bg-bg-card border border-border-gold flex items-center justify-center shadow-gold">
            <span className="text-gold font-[family-name:var(--font-heading)] font-bold text-lg">IV</span>
          </div>
          <div className="text-left">
            <h1 className="text-gold font-[family-name:var(--font-heading)] font-bold text-lg leading-tight tracking-wide">
              AoE4 Bot
            </h1>
            <p className="text-text-secondary text-xs font-[family-name:var(--font-body)]">
              Your AI Advisor for Age of Empires IV
            </p>
          </div>
        </button>
      </div>
      {/* Ornamental gold line */}
      <div className="ornament-line" />
    </header>
  );
}
