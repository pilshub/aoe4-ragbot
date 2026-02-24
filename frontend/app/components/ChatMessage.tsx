"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../lib/types";
import SourceCitation from "./SourceCitation";
import SuggestedQuestions from "./SuggestedQuestions";
import VortixRating from "./VortixRating";
import { useLang } from "../lib/LangContext";

// Age badge colors: detect Roman numerals in h3 headers
const AGE_COLORS: Record<number, { bg: string; border: string; text: string }> = {
  1: { bg: "rgba(120,120,120,0.12)", border: "rgba(120,120,120,0.4)", text: "#9a9284" },
  2: { bg: "rgba(201,168,76,0.12)", border: "rgba(201,168,76,0.5)", text: "#c9a84c" },
  3: { bg: "rgba(59,130,246,0.12)", border: "rgba(59,130,246,0.5)", text: "#7db4f5" },
  4: { bg: "rgba(168,85,247,0.12)", border: "rgba(168,85,247,0.5)", text: "#c4a1f0" },
};

function parseAgeFromHeader(text: string): number | null {
  // Match "IV" before "I" — order matters
  const m = text.match(/\b(IV|III|II|I)\b/);
  if (!m) return null;
  const map: Record<string, number> = { I: 1, II: 2, III: 3, IV: 4 };
  return map[m[1]] ?? null;
}

const markdownComponents: Components = {
  h3: ({ children, ...props }) => {
    const text = String(children);
    const age = parseAgeFromHeader(text);
    if (age && AGE_COLORS[age]) {
      const c = AGE_COLORS[age];
      return (
        <h3
          {...props}
          style={{
            background: c.bg,
            borderLeft: `3px solid ${c.border}`,
            padding: "0.35rem 0.75rem",
            borderRadius: "0 4px 4px 0",
            color: c.text,
            margin: "0.6rem 0 0.3rem",
          }}
        >
          {children}
        </h3>
      );
    }
    // Non-age h3 headers (Stats, Strategy, Matchup, etc.) — subtle gold style
    return (
      <h3
        {...props}
        style={{
          borderLeft: "3px solid rgba(201,168,76,0.3)",
          paddingLeft: "0.75rem",
          margin: "0.6rem 0 0.3rem",
        }}
      >
        {children}
      </h3>
    );
  },
};

// Matches rating lines like "Agresión: 5" or "- Agresión: 5" (ES and EN labels)
const RATING_LABELS: Record<string, string> = {
  "agresión": "AGR", "aggression": "AGR", "agresion": "AGR",
  "defensa": "DEF", "defense": "DEF",
  "infantería": "INF", "infantry": "INF", "infanteria": "INF",
  "a distancia": "RNG", "ranged": "RNG",
  "caballería": "CAV", "cavalry": "CAV", "caballeria": "CAV",
  "asedio": "SIE", "siege": "SIE",
  "monjes": "MON", "monks": "MON",
  "naval": "NAV",
  "comercio": "TRD", "trade": "TRD",
  "economía": "ECO", "economy": "ECO", "economia": "ECO",
};

const RATING_PATTERN = /(?:^|[-·•\n])[ \t]*([\wáéíóúñ][\wáéíóúñ ]*?):\s*(\d)\b/gi;
const RATING_SECTION = /(?:#{1,3}\s*)?(?:\*{0,2})(?:Valoraci[oó]n\s+de\s+Vortix|Vortix['']?s?\s+Rati?ng).*$/gim;

function extractRatings(content: string): { cleanContent: string; ratings: { label: string; value: number }[] | null } {
  // Find the rating section header
  const sectionMatch = content.match(RATING_SECTION);
  if (!sectionMatch) return { cleanContent: content, ratings: null };

  const sectionStart = content.indexOf(sectionMatch[0]);
  const ratingBlock = content.slice(sectionStart);

  // Extract individual ratings
  const ratings: { label: string; value: number }[] = [];
  let match;
  const re = new RegExp(RATING_PATTERN.source, RATING_PATTERN.flags);
  while ((match = re.exec(ratingBlock)) !== null) {
    const rawLabel = match[1].trim().toLowerCase();
    const shortLabel = RATING_LABELS[rawLabel];
    if (shortLabel) {
      ratings.push({ label: shortLabel, value: parseInt(match[2], 10) });
    }
  }

  if (ratings.length < 5) return { cleanContent: content, ratings: null };

  // Remove the rating section from the content
  const cleanContent = content.slice(0, sectionStart).trimEnd();
  return { cleanContent, ratings };
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  get_civ_stats: "civilization statistics",
  get_matchup_stats: "matchup data",
  get_map_stats: "map statistics",
  search_player: "player search",
  get_player_profile: "player profile",
  get_player_matches: "match history",
  get_leaderboard: "leaderboard",
  get_esports_leaderboard: "esports rankings",
  query_unit_stats: "unit data",
  query_building_stats: "building data",
  query_technology: "technology data",
  compare_units: "unit comparison",
  search_build_orders: "build orders",
  search_wiki: "wiki",
  get_wiki_page: "wiki page",
  search_liquipedia: "Liquipedia",
  get_ageup_stats: "age-up timings",
  search_pro_content: "pro player guides",
  get_patch_notes: "patch notes",
};

interface Props {
  message: Message;
  isLatest?: boolean;
  onFollowUp?: (text: string) => void;
}

export default function ChatMessage({ message, isLatest, onFollowUp }: Props) {
  const isUser = message.role === "user";
  const { t } = useLang();

  const activeToolName = message.activeTools?.length
    ? TOOL_DISPLAY_NAMES[message.activeTools[message.activeTools.length - 1]] ||
      message.activeTools[message.activeTools.length - 1].replace(/_/g, " ")
    : null;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-lg px-4 py-3 ${
          isUser
            ? "bg-[rgba(201,168,76,0.1)] border border-border-gold text-text-primary"
            : "card-medieval text-text-primary"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap font-[family-name:var(--font-body)]">{message.content}</p>
        ) : (
          <>
            {message.content ? (() => {
              const { cleanContent, ratings } = extractRatings(message.content);
              return (
                <>
                  <div className="chat-markdown text-sm">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                      {cleanContent}
                    </ReactMarkdown>
                  </div>
                  {ratings && <VortixRating ratings={ratings} />}
                </>
              );
            })() : (
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <span className="gold-pulse text-gold">&#9679;</span>
                <span className="font-[family-name:var(--font-body)] italic">
                  {activeToolName ? t.searching(activeToolName) : t.thinking}
                </span>
              </div>
            )}
            {isLatest && onFollowUp && message.content && !message.activeTools && (
              <SuggestedQuestions
                messageContent={message.content}
                onSelect={onFollowUp}
              />
            )}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-2 border-t border-border">
                <p className="text-xs text-text-dim mb-1.5 font-[family-name:var(--font-heading)] uppercase tracking-wider">{t.sources}</p>
                <div className="flex flex-wrap gap-1.5">
                  {message.sources.map((s, i) => (
                    <SourceCitation key={i} source={s} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
