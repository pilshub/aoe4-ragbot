"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../lib/types";
import SourceCitation from "./SourceCitation";
import SuggestedQuestions from "./SuggestedQuestions";

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
            {message.content ? (
              <div className="chat-markdown text-sm">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-text-secondary text-sm">
                <span className="gold-pulse text-gold">&#9679;</span>
                <span className="font-[family-name:var(--font-body)] italic">
                  {activeToolName ? `Querying ${activeToolName}...` : "Thinking..."}
                </span>
              </div>
            )}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-2 border-t border-border">
                <p className="text-xs text-text-dim mb-1.5 font-[family-name:var(--font-heading)] uppercase tracking-wider">Sources</p>
                <div className="flex flex-wrap gap-1.5">
                  {message.sources.map((s, i) => (
                    <SourceCitation key={i} source={s} />
                  ))}
                </div>
              </div>
            )}
            {isLatest && onFollowUp && message.content && !message.activeTools && (
              <SuggestedQuestions
                messageContent={message.content}
                onSelect={onFollowUp}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
