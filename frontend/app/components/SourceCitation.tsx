"use client";

import type { Source } from "../lib/types";

const TYPE_STYLES: Record<string, { bg: string; label: string }> = {
  aoe4world:  { bg: "bg-[rgba(59,130,246,0.12)] border-[rgba(59,130,246,0.25)] text-[#7db4f5]", label: "AoE4 World" },
  gamedata:   { bg: "bg-[rgba(34,197,94,0.12)] border-[rgba(34,197,94,0.25)] text-[#6dd4a0]", label: "Game Data" },
  aoe4guides: { bg: "bg-[rgba(168,85,247,0.12)] border-[rgba(168,85,247,0.25)] text-[#c4a1f0]", label: "AoE4 Guides" },
  wiki:       { bg: "bg-[rgba(201,168,76,0.12)] border-[rgba(201,168,76,0.25)] text-gold-light", label: "Wiki" },
  liquipedia: { bg: "bg-[rgba(6,182,212,0.12)] border-[rgba(6,182,212,0.25)] text-[#6ad4e8]", label: "Liquipedia" },
  youtube:    { bg: "bg-[rgba(255,0,0,0.12)] border-[rgba(255,0,0,0.25)] text-[#ff6b6b]", label: "YouTube" },
};

interface Props {
  source: Source;
}

export default function SourceCitation({ source }: Props) {
  const style = TYPE_STYLES[source.type] || { bg: "bg-bg-card border-border text-text-dim", label: source.type };

  const inner = (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border ${style.bg} font-[family-name:var(--font-body)]`}>
      <span className="opacity-60">{style.label}</span>
      <span className="opacity-40">|</span>
      <span>{source.title}</span>
    </span>
  );

  if (source.url) {
    return (
      <a href={source.url} target="_blank" rel="noopener noreferrer" className="no-underline hover:brightness-125 transition-all">
        {inner}
      </a>
    );
  }

  return inner;
}
