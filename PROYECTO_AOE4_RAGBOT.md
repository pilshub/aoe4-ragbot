# AoE4 RAGBot — Asistente IA para Age of Empires IV

## Estado: FASE 3 COMPLETADA + DESPLEGADO (24 Febrero 2026)

---

## Que es
Bot IA web que responde cualquier pregunta sobre Age of Empires IV usando datos en tiempo real de 4 APIs publicas gratuitas + una base de conocimiento con transcripts de YouTube de jugadores profesionales + 22 guias exclusivas escritas por Vortix. El LLM (GPT-4.1-mini) decide automaticamente que herramientas consultar (hasta 8 por turno) segun la pregunta y responde con datos actuales verificados, nunca inventados.

## Colaborador
- **Vortix** — Jugador profesional de AoE4, colaborador del proyecto. 22 guias de civilizaciones escritas por el.

---

## URLs de Produccion
- **Frontend:** https://aoe4-ragbot.vercel.app
- **Backend API:** https://aoe4-ragbot-production.up.railway.app
- **Health check:** https://aoe4-ragbot-production.up.railway.app/api/health
- **Repo GitHub:** https://github.com/pilshub/aoe4-ragbot (master)
- **Railway project:** elegant-healing (service: aoe4-ragbot)
- **Vercel project:** pilshubs-projects/aoe4-ragbot
- **Proyecto web adicional:** https://aoetest.vercel.app (quiz, tier list, build order editor, economy simulator, matchup calculator, roulette — proyecto Next.js separado)

## URLs Locales
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/api/health

## Arrancar
```bash
# Terminal 1 - Backend
cd aoe4-ragbot/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd aoe4-ragbot/frontend
npm install
npm run dev
```

**CUIDADO:** El puerto 8000 puede estar ocupado por MediaPulse (agentradar). Si el health check devuelve `{"detail":"Not authenticated"}`, es MediaPulse, no el AoE4 bot. Matar ese proceso primero:
```bash
netstat -ano | grep ":8000" | grep LISTENING
cmd //c "taskkill /PID <PID> /F"
```

## Deploy
```bash
# Backend → Railway
cd aoe4-ragbot/backend
railway login          # Solo si sesion expiro (interactivo, abre browser)
railway up --service aoe4-ragbot -d

# Frontend → Vercel
cd aoe4-ragbot/frontend
npx vercel deploy --prod --yes

# Push a GitHub
cd aoe4-ragbot
git add . && git commit -m "mensaje" && git push origin master
```

**CUIDADO Railway login:** La sesion de Railway CLI expira periodicamente. Si `railway up` devuelve "Unauthorized", hacer `railway login` manualmente en terminal (no funciona en non-interactive mode).

---

## Stack Tecnico
- **Backend:** Python 3.14, FastAPI, OpenAI API (GPT-4.1-mini), aiohttp, slowapi (rate limiting), sse-starlette
- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, react-markdown, remark-gfm, SSE
- **Knowledge Base:** SQLite + numpy (embeddings vectoriales, busqueda por similitud coseno)
- **Vortix Guides:** 22 archivos .md en `backend/data/guides/`, cargados desde disco (sin chunking)
- **Embeddings:** OpenAI text-embedding-3-small
- **Streaming:** Server-Sent Events (SSE) via sse-starlette
- **Cache:** TTL dict en memoria (cache.py) + cache de respuestas de civ guides en chat.py (1h TTL)
- **Game data:** JSONs de data.aoe4world.com cargados en memoria al arrancar
- **i18n:** ES/EN via LangContext + i18n.ts (frontend)

---

## APIs utilizadas (todas gratuitas, sin API key excepto OpenAI)

| API | URL | Que datos da |
|-----|-----|-------------|
| AoE4 World API | aoe4world.com/api/v0 | Winrates, matchups, mapas, jugadores, leaderboards, esports, patches |
| AoE4 World Data | data.aoe4world.com | Stats de unidades, edificios, tecnologias (JSON estatico) |
| AoE4 Guides API | aoe4guides.com | Build orders de la comunidad |
| Liquipedia | liquipedia.net/ageofempires/api.php | Torneos y esports |

**API eliminada:** Fandom Wiki (search_wiki, get_wiki_page) — eliminada por mediocre y datos duplicados.

---

## 17 Tools del LLM

### Estadisticas (AoE4 World API)
1. `get_civ_stats` — Winrate/pickrate de civilizaciones por modo, ELO, mapa, patch
2. `get_matchup_stats` — Civ vs civ head-to-head win rates
3. `get_map_stats` — Stats por mapa (juegos, mejores civs)
4. `get_ageup_stats` — Timings de age-up (feudal, castle, imperial) por civ y nivel

### Jugadores (AoE4 World API)
5. `search_player` — Buscar jugador por nombre
6. `get_player_profile` — Perfil completo (ratings, winrates)
7. `get_player_matches` — Historial de partidas recientes
8. `get_leaderboard` — Rankings ranked por modo
9. `get_esports_leaderboard` — Leaderboard de torneos/esports

### Game Data (data.aoe4world.com, cargado en memoria)
10. `query_unit_stats` — Stats detalladas de unidad (HP, dano, armor, coste, velocidad, rango)
11. `query_building_stats` — Stats de edificio/landmark
12. `query_technology` — Info de tecnologia (coste, tiempo, edificio, age)
13. `compare_units` — Comparar 2 unidades side-by-side

### Estrategia
14. `search_build_orders` — Build orders de aoe4guides.com
15. `search_pro_content` — **Tool principal de estrategia.** Cuando detecta civ en la query, carga la guia completa de Vortix desde disco (sin chunking, sin embedding). Cuando no detecta civ, busca semanticamente en 2,985 chunks de YouTube transcripts.

### Info General
16. `search_liquipedia` — Torneos, bios de pros, resultados
17. `get_patch_notes` — Version actual del patch y season

---

## Guias de Vortix (22 civilizaciones)

### Como funciona
- **22 archivos .md** en `backend/data/guides/` — uno por civilizacion
- Originales en .odt (Google Docs de Vortix), convertidos y pulidos a .md
- **Carga desde disco, sin chunking:** Cuando `search_pro_content` detecta una civ en la query, carga el .md completo (~4KB) como contexto. Sin perdida de informacion por chunking.
- **Skip embedding:** Cuando se carga guia desde disco, se SALTA la llamada a OpenAI embeddings (~500ms ahorrados)
- **Deteccion de civ:** Regex con ~60 aliases (ES/EN) ordenados por longitud (longest-first matching)

### Archivos
```
backend/data/guides/
├── abbasid_dynasty.md    ├── jeannes_darc.md
├── ayyubids.md           ├── knights_templar.md
├── byzantines.md         ├── macedonian_dynasty.md
├── chinese.md            ├── malians.md
├── delhi_sultanate.md    ├── mongols.md
├── english.md            ├── order_of_the_dragon.md
├── french.md             ├── ottomans.md
├── golden_horde.md       ├── rus.md
├── holy_roman_empire.md  ├── sengoku_daimyo.md
├── house_of_lancaster.md ├── tughlaq_dynasty.md
├── japanese.md           └── zhuxis_legacy.md
```

### Estructura de cada guia
Cada .md tiene: apertura, estrategia por edad (I-IV), matchups especificos, composiciones de ejercito, landmarks recomendados, y valoracion de Vortix (10 categorias del 1 al 5).

### Scripts de procesamiento
- `backend/scripts/ingest_guides.py` — Ingesta guias .md como chunks en SQLite (para queries sin civ detectada)
- `backend/scripts/polish_guides.py` — Limpieza y formato de las guias .md

### Deteccion de civ (knowledge_base.py)
```python
CIV_ALIASES: dict[str, str] = {
    "abbasid": "abbasid_dynasty", "bizantinos": "byzantines", "byz": "byzantines",
    "franceses": "french", "juana de arco": "jeannes_darc", "hre": "holy_roman_empire",
    "vikingos": None,  # No existe en AoE4
    # ... ~60 aliases total (ES + EN)
}
```

---

## Cache de Respuestas (chat.py)

### Como funciona
- **In-memory dict** con TTL de 1 hora
- **Cache key:** `{civ_id}:{language}` (ej: `french:es`, `mongols:en`)
- **Cuando cachea:** Queries de un solo mensaje que mencionan una civ y no son de matchup/counter/stats
- **Que cachea:** Todos los SSE events (tokens + sources + done)
- **Replay:** En cache hit, los events se emiten instantaneamente sin llamar a OpenAI
- **Resultado:** Primera query ~10s, segunda query ~0.9s (99% reduccion)
- **No cachea:** Errores, queries multi-turno, queries sin civ detectada

### Exclusiones del cache
Queries con estas palabras NO se cachean (son dinamicas): `vs`, `contra`, `counter`, `win rate`, `winrate`, `stats`, `build order`, `matchup`, `parche`, `patch`, `nerf`, `buff`

---

## Knowledge Base (YouTube Transcripts)

### Datos actuales
- **Total chunks:** 2,985 (2,776 YouTube + 209 guide chunks)
- **Total videos ingested:** 208 de 231 aprobados (23 sin transcript disponible)
- **DB file:** `backend/data/knowledge.db` (24 MB, SQLite)

### Distribucion por canal
| Canal | Videos | Chunks | Idioma |
|-------|--------|--------|--------|
| Vortix | 83 | 1,066 | Español |
| Valdemar | 81 | 804 | Ingles |
| MarineLorD | 38 | 591 | Ingles (auto-traducido del frances) |
| Beastyqt | 29 | 315 | Ingles |
| Vortix guides | 22 | 209 | Español (chunks de guias .md) |

### Como funciona la busqueda
1. **Con civ detectada:** Carga guia .md completa desde disco. NO hace embedding. Rapido (~0ms).
2. **Sin civ detectada:** Genera embedding del query con OpenAI, busca cosine similarity en SQLite con numpy, devuelve top 5 chunks.

### Comandos de ingesta
```bash
cd backend
python -m scripts.scrape_youtube           # Buscar videos nuevos
python -m scripts.ingest_videos            # Procesar videos aprobados
python -m scripts.ingest_videos --reset    # Re-ingestar todo
python -m scripts.update_knowledge         # Update incremental
```

---

## Frontend — Elementos Visuales

### Radar Chart (VortixRating.tsx)
- SVG puro (200x200) con 10 ejes: AGR, DEF, INF, RNG, CAV, SIE, MON, NAV, TRD, ECO
- Hover tooltips con nombre completo (ES/EN) + valor/5
- Glow dorado en punto hover
- Animacion fade-in (scale 0.85→1)
- Se extrae automaticamente de la respuesta markdown ("Valoracion de Vortix" / "Vortix Rating")

### Age Badges (ChatMessage.tsx)
- Headers h3 con numeros romanos (I-IV) detectados automaticamente
- Colores por edad:
  - I (Dark Age): gris `rgba(120,120,120)`
  - II (Feudal): dorado `rgba(201,168,76)`
  - III (Castle): azul `rgba(59,130,246)`
  - IV (Imperial): purpura `rgba(168,85,247)`
- Headers h3 sin numeros romanos: borde dorado sutil a la izquierda

### Suggested Questions (SuggestedQuestions.tsx)
- Patrones regex detectan tipo de respuesta (strategy, winrate, buildOrder, unit, counter, leaderboard, patch)
- Muestra hasta 3 preguntas sugeridas con fondo dorado sutil
- Se muestran ANTES de las fuentes

### Markdown Styling (globals.css)
- **h2/h3:** Fuente Cinzel, color dorado
- **strong/bold:** Color dorado claro (gold-light)
- **Bullets:** Marcadores dorado oscuro, disc/circle para anidados
- **Tablas:** Headers con fondo dorado, filas alternas
- **Links:** Color dorado con subrayado
- **Blockquotes:** Borde izquierdo dorado, fondo sutil, cursiva
- **HR:** Gradiente dorado transparente→dorado→transparente
- **Codigo:** Fondo oscuro con borde

### i18n (LangContext.tsx + i18n.ts)
- Soporte ES/EN con deteccion automatica del navegador
- Toggle en el header
- Traducciones: thinking, searching, sources, relatedQuestions, welcome, placeholders, suggested questions

### Fuentes (Source Citations)
- Color-coded por tipo: aoe4world (azul), youtube (rojo), guide (dorado), gamedata (verde), liquipedia (purpura)

---

## System Prompt (chat.py)

El system prompt esta en `backend/chat.py` (variable SYSTEM_PROMPT). Secciones clave:

### Reglas criticas
1. **CRITICAL RULE:** NUNCA hacer claims sobre mecanicas sin verificar con tools
2. **NUNCA inventar build orders.** Siempre usar `search_build_orders`
3. **CRITICAL — Match language:** Ingles → respuesta en ingles. Traducir guias de Vortix del espanol

### Formato de respuestas
- **Ages:** `### I — Primera Edad`, `### II — Feudal`, `### III — Castillos`, `### IV — Imperial` (ES)
- **Ages:** `### I — Dark Age`, `### II — Feudal`, `### III — Castle`, `### IV — Imperial` (EN)
- NUNCA decir "Segunda Edad", "Tercera Edad", "Cuarta Edad"
- **Visual elements en TODAS las respuestas:** headers ###, bold, bullets, tables, dividers ---
- **Conciseness:** 150-250 palabras max para guias de civ

### Estructura obligatoria para guias de civ
1. Una frase intro (identidad de la civ)
2. `### I — Primera Edad / Dark Age`
3. `### II — Feudal`
4. `### III — Castillos / Castle`
5. `### IV — Imperial`
6. `### V — Matchups` ← OBLIGATORIO. Incluir TODOS los matchups de la guia
7. `### Valoracion de Vortix` ← OBLIGATORIO. 10 categorias separadas por ·

### Secciones especiales
- **Key Counter Relationships:** Springald→siege, Spearman→cavalry, Horseman→ranged, etc.
- **Civilization Passive Bonuses:** English Network of Castles, Mongols Nomadic, etc.
- **Non-AoE4 Civilizations:** Lista ampliada con nombres en espanol (Vikingos, Aztecas, Celtas, etc.)
- **Variant Civilizations:** 10 variantes con diferencias clave
- **Core Game Mechanics:** Victory conditions, Sacred Sites, Ages, Wonders
- **Tone:** "Like a friend who's also a pro" — natural, directo, no robotico

---

## Estructura de Archivos

```
aoe4-ragbot/
├── PROYECTO_AOE4_RAGBOT.md          ← ESTE ARCHIVO
├── test_50.py                       ← Test suite round 1 (50 queries)
├── test_50b.py                      ← Test suite round 2 (50 queries)
├── backend/
│   ├── .env                         ← OPENAI_API_KEY, APIFY_API_TOKEN
│   ├── requirements.txt
│   ├── Procfile                     ← Railway: web: uvicorn main:app ...
│   ├── main.py                      ← FastAPI app, lifespan, endpoints
│   ├── chat.py                      ← SYSTEM_PROMPT + chat_stream() + response cache
│   ├── config.py                    ← API keys, URLs, cache TTLs, civ mappings, model
│   ├── models.py                    ← Pydantic: ChatRequest, Source
│   ├── cache.py                     ← TTL cache en memoria (para API responses)
│   ├── utils.py                     ← fetch_json(), close_session()
│   ├── knowledge/
│   │   └── __init__.py              ← SQLite vector store (search, upsert, count)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                ← Carga JSONs de data.aoe4world.com al arrancar
│   │   ├── game_store.py            ← GameStore: busqueda fuzzy de unidades/edificios/techs
│   │   ├── glossary.py              ← Expansion de abreviaciones gaming
│   │   ├── guides/                  ← 22 guias .md de Vortix (una por civ)
│   │   ├── cache/                   ← Cache de JSONs de game data (gitignored)
│   │   ├── knowledge.db             ← SQLite con 2,985 chunks + embeddings (gitignored)
│   │   ├── video_candidates.json    ← Catalogo de videos scrapeados (gitignored)
│   │   └── transcript_cache.json    ← Cache de transcripts Apify (gitignored)
│   ├── tools/
│   │   ├── __init__.py              ← TOOL_REGISTRY (17 tools)
│   │   ├── definitions.py           ← TOOL_DEFINITIONS (JSON schemas para OpenAI)
│   │   ├── aoe4world_stats.py       ← get_civ_stats, get_matchup_stats, get_map_stats
│   │   ├── aoe4world_players.py     ← search_player, get_player_profile, get_player_matches
│   │   ├── aoe4world_leaderboards.py← get_leaderboard
│   │   ├── aoe4world_esports.py     ← get_esports_leaderboard
│   │   ├── aoe4world_patches.py     ← get_patch_notes
│   │   ├── game_data.py             ← query_unit_stats, query_building_stats, etc.
│   │   ├── build_orders.py          ← search_build_orders
│   │   ├── liquipedia.py            ← search_liquipedia
│   │   ├── knowledge_base.py        ← search_pro_content + civ detection + guide loading
│   │   ├── ageups.py                ← get_ageup_stats
│   │   └── wiki.py                  ← EXISTE pero NO registrada (eliminada)
│   └── scripts/
│       ├── scrape_youtube.py        ← Scraping de videos YouTube
│       ├── ingest_videos.py         ← Ingesta: transcripts → chunks → embeddings → SQLite
│       ├── ingest_guides.py         ← Ingesta guias .md → chunks en SQLite
│       ├── polish_guides.py         ← Limpieza y formato de guias .md
│       └── update_knowledge.py      ← Update incremental knowledge base
├── frontend/
│   ├── package.json
│   ├── next.config.ts               ← Rewrites /api/* → backend
│   ├── .env.local                   ← NEXT_PUBLIC_API_URL
│   └── app/
│       ├── layout.tsx               ← LangProvider wrapper
│       ├── page.tsx
│       ├── globals.css              ← Theme medieval oscuro, markdown styling
│       ├── components/
│       │   ├── ChatInterface.tsx     ← Componente principal del chat
│       │   ├── ChatMessage.tsx       ← Render mensajes: markdown, age badges, rating extraction
│       │   ├── ChatInput.tsx         ← Input de texto + boton enviar
│       │   ├── Header.tsx            ← Header con titulo + language toggle
│       │   ├── VortixRating.tsx      ← SVG radar chart con hover tooltips
│       │   ├── SourceCitation.tsx    ← Citations color-coded por tipo
│       │   ├── SuggestedQuestions.tsx ← Preguntas sugeridas basadas en respuesta
│       │   └── WelcomeScreen.tsx     ← Pantalla inicial con ejemplos
│       └── lib/
│           ├── types.ts             ← Message, Source interfaces
│           ├── LangContext.tsx       ← React context para i18n
│           └── i18n.ts              ← Traducciones ES/EN
```

---

## Credenciales

- **OpenAI API Key:** En `backend/.env` como `OPENAI_API_KEY`
- **Apify API Token:** En `backend/.env` como `APIFY_API_TOKEN` (para transcripts YouTube)
- **Resto de APIs:** No necesitan key (AoE4 World, AoE4 Guides, Liquipedia son publicas)

---

## Costes

### Por consulta
- **GPT-4.1-mini:** ~$0.003 por query (input $0.40/1M tokens, output $1.60/1M tokens)
- **Embedding (solo queries sin civ):** ~$0.00002 por query
- **Cache hit (civ repetida):** $0.00 (respuesta desde memoria)
- **APIs externas:** $0 (todas gratuitas)

### Test de 100 queries
- 100 queries diversas: **~$0.54** total (~$0.005/query)
- 50 queries round 1: $0.27 en ~7 minutos
- 50 queries round 2: $0.27 en ~5.5 minutos

### Estimacion mensual
| Escenario | Queries/dia | Coste OpenAI/mes | Infra/mes | Total/mes |
|-----------|-------------|------------------|-----------|-----------|
| Testing | 20 | ~$2 | $5 | ~$7 |
| 100 usuarios | 300 | ~$27 | $5 | ~$32 |
| 500 usuarios | 1500 | ~$135 | $10 | ~$145 |

*Con cache activado, queries de civ repetidas cuestan $0. En uso real, ~40% de queries son de civs, asi que el coste real es ~60% del estimado.*

---

## Configuracion clave (config.py)

- **Modelo LLM:** `gpt-4.1-mini` (cambiado de gpt-5-mini por velocidad)
- **Max tool calls por turno:** 8
- **Rate limit API:** 20 requests/min por IP (slowapi)
- **Cache TTLs:** Stats 1h, Players 5min, Builds 1h, Liquipedia 1h, **Civ guide responses 1h**
- **22 civilizaciones** con aliases en espanol e ingles (~60 aliases)
- **Glosario de abreviaciones:** maa, xbow, fc, tc, bo, etc.

---

## Testing (100 queries, 0 errores)

### Round 1 (50 queries)
- **50/50 OK**, 0 errores
- Civ guides (22): 22/22 ages, 22/22 matchups, 22/22 ratings, 0 bad age names
- Avg time: 8.4s (civ guides 9.0s, non-civ 5.5s)
- 1 outlier: Man-at-Arms 65.5s (one-off, 5.5s on retry)

### Round 2 (50 queries)
- **50/50 OK**, 0 errores
- Civ guides (10): 9/10 ages (1 fallo por phrasing vago), 0 bad age names
- Avg time: 6.6s
- Issues: "Britons guide" no rechazado como non-AoE4 (edge case)

### Tiempos por categoria (100 queries)
| Categoria | Avg Time |
|-----------|----------|
| Civ Guides | 9.0s (0.9s con cache) |
| Counters/Matchups | 7.0s |
| Strategy/Meta | 7.1s |
| Build Orders | 7.5s |
| Pro Opinions | 6.4s |
| Players | 5.2s |
| Game Data | 4.2s |
| Mechanics | 3.4s |
| Edge Cases | 4.0s |

### Bugs encontrados en testing
1. **"Vikingos" no rechazado** como non-AoE4 → Fixed: lista ampliada con nombres ES
2. **"Britons guide"** devolvio guia de English en vez de rechazar → Parcialmente fixed en prompt
3. **"Que hago con abasidas"** no genero estructura de guia → Phrasing demasiado vago, edge case aceptable
4. **Idioma mezclado** (EN question → ES response) → Fixed: prompt reforzado con CRITICAL language matching

---

## Historial de cambios

### Fase 1 (completada)
- Backend FastAPI con 16 tools
- Frontend Next.js con chat streaming
- 5 APIs gratuitas conectadas
- System prompt basico
- Cache en memoria

### Fase 2 (completada — 19-20 Febrero 2026)
- Knowledge base SQLite + numpy (2,776 chunks de YouTube)
- 4 canales: Beastyqt, Valdemar, Vortix, MarineLorD
- QA exhaustivo: 24 rounds, ~200 queries, 22 bugs corregidos
- Upgrade GPT-4.1-mini → GPT-5-mini (luego revertido)

### Fase 3 (completada — 24 Febrero 2026)
**Vortix Guides:**
- 22 guias de civilizacion (.odt → .md), ~4KB cada una
- Carga desde disco (sin chunking, sin perdida de info)
- Skip embedding call cuando civ detectada (~500ms ahorrado)
- 209 chunks adicionales en knowledge.db para queries sin civ
- Deteccion de civ via regex con ~60 aliases ES/EN

**Response Cache:**
- In-memory cache por (civ_id, language), TTL 1 hora
- Primera query ~10s, cache hit ~0.9s (99% reduccion)
- No cachea: errores, multi-turno, queries sin civ, matchups

**Visual Polish (frontend):**
- SVG radar chart para Vortix ratings (10 ejes, hover tooltips)
- Age badges con colores por edad (gris/dorado/azul/purpura)
- Non-age h3 headers con borde dorado sutil
- Blockquote styling para citas de pros
- Bullets visibles (fix Tailwind CSS reset)
- Suggested questions con fondo dorado, encima de fuentes
- Markdown styling: tablas, links, code, HR, bold todo en gold theme

**i18n:**
- ES/EN con deteccion automatica + toggle manual
- LangContext + i18n.ts con traducciones completas

**System Prompt:**
- Estructura obligatoria: I-IV + V Matchups + Valoracion de Vortix
- Age headers estandarizados (nunca "Segunda Edad")
- Language matching reforzado (traducir guias ES→EN)
- Non-AoE4 civs ampliado con nombres en espanol
- Formatting: ### headers + bold + bullets + tables + --- en TODAS las respuestas
- Tono natural ("like a friend who's a pro")
- Conciseness: 150-250 palabras max

**Modelo:**
- GPT-5-mini → GPT-4.1-mini (mas rapido, mismo coste)

**Deploy:**
- Backend en Railway (elegant-healing)
- Frontend en Vercel (aoe4-ragbot)
- GitHub repo: pilshub/aoe4-ragbot

**Testing:**
- 100 queries en 2 rounds, 0 errores
- 31/32 civ guides con estructura completa (96.9%)
- 0 bad age names
- Avg time: 7.5s (0.9s con cache)

---

## Problemas conocidos

### Railway session expira
- **Problema:** `railway login` expira periodicamente, `railway up` devuelve "Unauthorized"
- **Solucion:** `railway login` manualmente en terminal (interactivo, abre browser)

### "Britons guide" no siempre rechazado
- **Problema:** En vez de decir "Britons no existe en AoE4", a veces devuelve la guia de English diciendo "historically corresponds to Britons"
- **Solucion parcial:** Prompt reforzado. Edge case dificil porque el LLM intenta ser util.

### Puerto 8000 ocupado por MediaPulse
- **Problema:** MediaPulse (agentradar) usa mismo puerto
- **Solucion:** Verificar health check, matar proceso incorrecto

---

## Modelo de Negocio

### Decision: Academia Discord + Web complementaria
- **Concepto:** "AoE4 Academy" con Vortix como pro player residente
- **Plataforma pagos:** Whop.com (3% comision, vincula roles Discord)
- **Tiers:** Free (5/dia), Member (4.99€/mes, ilimitado), Pro (9.99€/mes, coaching), VIP (24.99€/mes, sesion con Vortix)

---

## Pendiente (Fase 4)

### Alta prioridad
1. **Bot de Discord** — discord.py conectado al backend, limites por tier
2. **Autenticacion** — Discord OAuth para web + unificar identidad
3. **Whop.com** — Configurar tiers y vincular Discord

### Media prioridad
4. **Calculadora de produccion** — Tool nueva: cuantos aldeanos por recurso para producir X unidad
5. **Mobile optimization** — Verificar y pulir responsive
6. **Mas canales YouTube** — Considerar Drongo, Spirit of the Law
7. **Auto-update knowledge base** — Cron para ingestar videos nuevos automaticamente

### Baja prioridad
8. **Historial en localStorage** — Guardar ultimos 50 mensajes
9. **Response streaming optimizado** — Comprimir SSE events
10. **Analytics** — Tracking de queries populares para mejorar el bot

---

## Para retomar
1. Leer este archivo (PROYECTO_AOE4_RAGBOT.md)
2. `cd aoe4-ragbot/backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000`
3. `cd aoe4-ragbot/frontend && npm run dev`
4. Probar en http://localhost:3000
5. Deploy: `railway up` (backend) + `npx vercel deploy --prod` (frontend)
