export type Lang = "en" | "es";

const translations = {
  en: {
    // Header
    headerTitle: "AoE4 Bot",
    headerSubtitle: "Your AI Advisor for Age of Empires IV",

    // Welcome
    welcomeDescription:
      "Ask me anything about Age of Empires IV — civilizations, strategies, unit stats, build orders, pro players, win rates, and more.",

    // Examples
    examples: [
      { text: "What's the best counter to French Knights?", icon: "⚔" },
      { text: "Show me English Fast Castle build orders", icon: "🏰" },
      { text: "Who is #1 on the ranked leaderboard?", icon: "👑" },
      { text: "Compare Longbowman vs Archer stats", icon: "🏹" },
      { text: "What is the current win rate of Mongols?", icon: "📊" },
      { text: "How do I play Ottomans in 1v1?", icon: "✦" },
    ],

    // Input
    placeholder: "Ask about AoE4...",
    send: "Send",
    stop: "Stop",

    // Messages
    thinking: "Thinking...",
    searching: (tool: string) => `Searching ${tool}...`,
    sources: "Sources",
    relatedQuestions: "Related Questions",

    // Suggested questions
    suggestions: {
      winrate: [
        "Show me the matchups against the top civs",
        "What are the best build orders for this civ?",
        "How does this compare in team games?",
      ],
      buildOrder: [
        "What are the key timings for this build?",
        "What counters this strategy?",
        "Any pro player tips for this approach?",
      ],
      unit: [
        "What counters this unit?",
        "Compare this with similar units",
        "What upgrades improve this unit?",
      ],
      counter: [
        "Show me a build order for this matchup",
        "What do pro players recommend?",
        "What's the win rate in this matchup?",
      ],
      leaderboard: [
        "What civilization does the #1 player main?",
        "Show me the esports tournament rankings",
        "Who are the top players from Spain?",
      ],
      patch: [
        "Which civs are strongest this season?",
        "Show me the current tier list",
        "What changed for my main civ?",
      ],
      strategy: [
        "Show me build orders for this civ",
        "What's the current win rate?",
        "What are the age-up timings?",
      ],
    },
  },
  es: {
    headerTitle: "AoE4 Bot",
    headerSubtitle: "Tu Asistente IA para Age of Empires IV",

    welcomeDescription:
      "Pregúntame lo que quieras sobre Age of Empires IV — civilizaciones, estrategias, stats de unidades, build orders, jugadores pro, winrates y más.",

    examples: [
      { text: "¿Cuál es el mejor counter a los Caballeros Franceses?", icon: "⚔" },
      { text: "Enséñame build orders de Fast Castle con Ingleses", icon: "🏰" },
      { text: "¿Quién es el #1 en el ranking?", icon: "👑" },
      { text: "Compara el Longbowman con el Arquero", icon: "🏹" },
      { text: "¿Qué winrate tienen los Mongoles ahora?", icon: "📊" },
      { text: "¿Cómo juego Otomanos en 1v1?", icon: "✦" },
    ],

    placeholder: "Pregunta sobre AoE4...",
    send: "Enviar",
    stop: "Parar",

    thinking: "Pensando...",
    searching: (tool: string) => `Buscando ${tool}...`,
    sources: "Fuentes",
    relatedQuestions: "Preguntas Relacionadas",

    suggestions: {
      winrate: [
        "Muéstrame los matchups contra las mejores civs",
        "¿Cuáles son los mejores build orders para esta civ?",
        "¿Cómo le va en partidas de equipo?",
      ],
      buildOrder: [
        "¿Cuáles son los timings clave de este build?",
        "¿Qué countera esta estrategia?",
        "¿Algún consejo de pros para esta apertura?",
      ],
      unit: [
        "¿Qué countera a esta unidad?",
        "Compara con unidades similares",
        "¿Qué mejoras tiene esta unidad?",
      ],
      counter: [
        "Enséñame un build order para este matchup",
        "¿Qué recomiendan los pros?",
        "¿Cuál es el winrate en este matchup?",
      ],
      leaderboard: [
        "¿Qué civilización juega el #1?",
        "Muéstrame el ranking de torneos esports",
        "¿Quiénes son los mejores jugadores de España?",
      ],
      patch: [
        "¿Qué civs son las más fuertes esta temporada?",
        "Muéstrame la tier list actual",
        "¿Qué cambiaron en mi civ?",
      ],
      strategy: [
        "Enséñame build orders de esta civ",
        "¿Cuál es el winrate actual?",
        "¿Cuáles son los timings de subida de edad?",
      ],
    },
  },
};

export type Translations = typeof translations.en;

export function getTranslations(lang: Lang): Translations {
  return translations[lang] as Translations;
}

export function detectBrowserLang(): Lang {
  if (typeof navigator === "undefined") return "en";
  const browserLang = navigator.language?.slice(0, 2);
  return browserLang === "es" ? "es" : "en";
}
