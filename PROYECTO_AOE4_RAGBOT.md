# AoE4 RAGBot — Asistente IA para Age of Empires IV

## Estado: FASE 2 COMPLETADA + QA TESTING (20 Febrero 2026)

---

## Que es
Bot IA web que responde cualquier pregunta sobre Age of Empires IV usando datos en tiempo real de 4 APIs publicas gratuitas + una base de conocimiento con transcripts de YouTube de jugadores profesionales. El LLM (GPT-4.1-mini) decide automaticamente que herramientas consultar segun la pregunta y responde con datos actuales verificados, nunca inventados.

## Colaborador
- **Vortix** — Jugador profesional de AoE4, colaborador del proyecto. Guias y validacion de contenido.

---

## URLs
- **Frontend:** http://localhost:3000 (o :3001 si 3000 esta ocupado)
- **Backend API:** http://localhost:8000
- **Health check:** http://localhost:8000/api/health
- **Proyecto web adicional:** https://aoetest.vercel.app (quiz, tier list, build order editor, economy simulator, matchup calculator, roulette — proyecto Next.js separado)

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
# Ver que proceso usa el puerto
netstat -ano | grep ":8000" | grep LISTENING
# Matar el proceso incorrecto
cmd //c "taskkill /PID <PID> /F"
```

---

## Stack Tecnico
- **Backend:** Python 3.14, FastAPI, OpenAI API (GPT-4.1-mini), aiohttp, slowapi (rate limiting)
- **Frontend:** Next.js 16, React, Tailwind CSS v4, react-markdown, SSE
- **Knowledge Base:** SQLite + numpy (embeddings vectoriales, busqueda por similitud coseno)
- **Embeddings:** OpenAI text-embedding-3-small
- **Streaming:** Server-Sent Events (SSE) via sse-starlette
- **Cache:** TTL dict en memoria (cache.py)
- **Game data:** JSONs de data.aoe4world.com cargados en memoria al arrancar

---

## APIs utilizadas (todas gratuitas, sin API key excepto OpenAI)

| API | URL | Que datos da |
|-----|-----|-------------|
| AoE4 World API | aoe4world.com/api/v0 | Winrates, matchups, mapas, jugadores, leaderboards, esports, patches |
| AoE4 World Data | data.aoe4world.com | Stats de unidades, edificios, tecnologias (JSON estatico) |
| AoE4 Guides API | aoe4guides.com | Build orders de la comunidad |
| Liquipedia | liquipedia.net/ageofempires/api.php | Torneos y esports |

**API eliminada:** Fandom Wiki (search_wiki, get_wiki_page) — eliminada por mediocre y datos duplicados con otras tools.

**Nota sobre AoE4 World:** Proyecto open source hecho por Rene Klacan (Eslovaquia) y Robert van Hoesel (Holanda, CEO de FirstLook/Pragma). 12M+ pageviews/ano. Se financian con donaciones Ko-fi (ko-fi.com/aoe4world). Datos publicos, piden atribucion.

---

## 16 Tools del LLM

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
10. `query_unit_stats` — Stats detalladas de unidad (HP, daño, armor, coste, velocidad, rango)
11. `query_building_stats` — Stats de edificio/landmark
12. `query_technology` — Info de tecnologia (coste, tiempo, edificio, age)
13. `compare_units` — Comparar 2 unidades side-by-side

### Estrategia
14. `search_build_orders` — Build orders de aoe4guides.com
15. `search_pro_content` — **Tool principal de estrategia.** Busca en 2,776 chunks de transcripts de YouTube de pros (Beastyqt, Valdemar, Vortix, MarineLorD). Devuelve extractos con links timestamp a YouTube.

### Info General
16. `search_liquipedia` — Torneos, bios de pros, resultados (rate limited: 2s entre requests)

### Tool eliminada (Fase 2)
- ~~`get_patch_notes`~~ — Sigue en el codigo pero da info limitada (solo version de patch, no notas detalladas)

**Nota:** `get_patch_notes` esta registrada como tool 16. `search_liquipedia` es la 16 en la lista pero el total es 16 tools activas.

**Archivos de tools:**
- `backend/tools/__init__.py` — Registro de tools (TOOL_REGISTRY dict)
- `backend/tools/definitions.py` — JSON schemas para OpenAI (TOOL_DEFINITIONS list)
- `backend/tools/wiki.py` — EXISTE pero NO esta registrada (eliminada del registry y definitions)

---

## Knowledge Base (YouTube Transcripts)

### Datos actuales
- **Total chunks:** 2,776
- **Total videos ingested:** 208 de 231 aprobados (23 sin transcript disponible)
- **Videos scrapeados:** 236 candidatos (ultimos 12 meses)
- **DB file:** `backend/data/knowledge.db` (24 MB, SQLite)
- **Transcript cache:** `backend/data/transcript_cache.json` (4.4 MB)
- **Video catalog:** `backend/data/video_candidates.json` (80 KB)

### Distribucion por canal
| Canal | Videos | Chunks | Idioma |
|-------|--------|--------|--------|
| Vortix | 83 aprobados | 1,066 | Español (es) |
| Valdemar | 81 aprobados | 804 | Ingles (en) |
| MarineLorD | 38 aprobados | 591 | Ingles (en, auto-traducido del frances) |
| Beastyqt | 29 aprobados | 315 | Ingles (en) |

### Como funciona
1. **Scraping:** `python -m scripts.scrape_youtube` — usa yt-dlp para listar videos de 4 canales, filtra por keywords (guide, tier list, build order, strategy, etc.) y duracion (3-60 min)
2. **Ingesta:** `python -m scripts.ingest_videos` — descarga transcripts via Apify (karamelo~youtube-transcripts), chunking 500 tokens con 50 overlap, embedding con text-embedding-3-small, almacena en SQLite
3. **Busqueda:** `search_pro_content(query, channel?, language?)` — genera embedding del query, busca cosine similarity en SQLite con numpy, devuelve top 5 chunks

### Apify (transcripts de YouTube)
- **Actor:** `karamelo~youtube-transcripts`
- **Coste:** ~$0.005 por video
- **Batch size:** 25 videos por llamada
- **API key:** En `backend/.env` como `APIFY_API_TOKEN`
- **Cache:** Transcripts se cachean en `transcript_cache.json` para no re-descargar
- **Por que Apify:** youtube-transcript-api funciona pero YouTube bloquea la IP tras ~25 descargas rapidas (429 rate limit). Apify usa proxies y no tiene ese problema.

### Comandos de ingesta
```bash
cd backend

# Scrape: buscar videos nuevos (ultimos 365 dias por defecto)
python -m scripts.scrape_youtube
python -m scripts.scrape_youtube --days 365

# Ingest: procesar videos aprobados
python -m scripts.ingest_videos
python -m scripts.ingest_videos --reset    # Re-ingestar todo desde cero
python -m scripts.ingest_videos --no-apify  # Usar youtube-transcript-api directo (puede dar 429)

# Update: buscar e ingestar videos nuevos (incremental)
python -m scripts.update_knowledge
python -m scripts.update_knowledge --dry-run
```

### Schema de SQLite (knowledge.db)
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,           -- "{video_id}_chunk_{n}"
    document TEXT NOT NULL,        -- Texto del chunk
    embedding BLOB NOT NULL,       -- float32 array como bytes
    source TEXT NOT NULL,          -- "youtube"
    channel TEXT,                  -- "Beastyqt", "Valdemar", "Vortix", "MarineLorD"
    title TEXT,                    -- Titulo del video
    video_id TEXT,                 -- ID de YouTube
    url TEXT,                      -- URL con timestamp (&t=XXX)
    upload_date TEXT,              -- "YYYYMMDD"
    language TEXT,                 -- "en" o "es"
    timestamp_start INTEGER,       -- Segundo de inicio del chunk
    timestamp_end INTEGER          -- Segundo de fin del chunk
);
CREATE INDEX idx_chunks_video_id ON chunks(video_id);
CREATE INDEX idx_chunks_channel ON chunks(channel);
```

---

## System Prompt (reglas criticas)

El system prompt esta en `backend/chat.py` (variable SYSTEM_PROMPT). Reglas clave:

1. **CRITICAL RULE:** NUNCA hacer claims sobre mecanicas del juego sin verificar con tools. El LLM puede inventar datos incorrectos (ej: "archers counter knights" es FALSO — los crossbowmen tienen bonus anti-armor, los archers no).
2. **NUNCA inventar build orders.** Siempre usar `search_build_orders`. Si no hay resultados, recomendar aoe4guides.com.
3. **Prioridad de respuesta:** (1) Datos reales de tools, (2) Advice de pros via `search_pro_content`, (3) Build orders via `search_build_orders`.
4. **`search_pro_content` es la tool principal de estrategia** — usar para CUALQUIER pregunta de estrategia, counters, meta, "como jugar".
5. **Filtro por canal:** Cuando el usuario menciona un pro especifico, pasar `channel="Vortix"` (o el que sea). Vortix es espanol → `language="es"`.
6. **Citar fuentes:** Links a YouTube con timestamps, datos de aoe4world.com con sample sizes.

### Secciones especiales del prompt (anadidas en QA)
- **Key Counter Relationships:** Springald→siege, Spearman→cavalry, Horseman→ranged, etc. El API no muestra todos los bonus damage, asi que el prompt incluye counters verificados.
- **Civilization Passive Bonuses:** English Network of Castles (25% attack speed), Mongols Nomadic (packed buildings, no walls), French Royal Influence, Chinese Dynasty System, Delhi Scholar System, Rus Bounty System, HRE Prelate Inspiration. Estos bonuses pasivos no estan en buildings/technologies del API.
- **Non-AoE4 Civilizations:** Lista de 22 civs del juego. Instruccion de rechazar civs que no existen (Aztecs, Mayans, etc.) y sugerir en que juego AoE estan.
- **Meta questions:** Instruccion explicita de usar `get_civ_stats` + `search_pro_content` para preguntas de meta/best civs.

---

## Estructura de Archivos

```
aoe4-ragbot/
├── .gitignore
├── PROYECTO_AOE4_RAGBOT.md          ← ESTE ARCHIVO
├── backend/
│   ├── .env                         ← OPENAI_API_KEY, APIFY_API_TOKEN
│   ├── requirements.txt
│   ├── main.py                      ← FastAPI app, lifespan, endpoints
│   ├── chat.py                      ← SYSTEM_PROMPT + chat_stream() con tool loop
│   ├── config.py                    ← API keys, URLs, cache TTLs, civ mappings
│   ├── models.py                    ← Pydantic: ChatRequest, Source, ChatResponseChunk
│   ├── cache.py                     ← TTL cache en memoria
│   ├── utils.py                     ← fetch_json(), close_session()
│   ├── knowledge/
│   │   └── __init__.py              ← SQLite vector store (search, upsert, count)
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                ← Carga JSONs de data.aoe4world.com al arrancar
│   │   ├── game_store.py            ← GameStore: busqueda fuzzy de unidades/edificios/techs
│   │   ├── glossary.py              ← Expansion de abreviaciones gaming (maa→Man-at-Arms)
│   │   ├── cache/                   ← Cache de JSONs de game data (gitignored)
│   │   ├── knowledge.db             ← SQLite con 2,776 chunks + embeddings (24 MB, gitignored)
│   │   ├── video_candidates.json    ← Catalogo de 236 videos scrapeados (gitignored)
│   │   └── transcript_cache.json    ← Cache de transcripts de Apify (4.4 MB, gitignored)
│   ├── tools/
│   │   ├── __init__.py              ← TOOL_REGISTRY (16 tools registradas)
│   │   ├── definitions.py           ← TOOL_DEFINITIONS (JSON schemas para OpenAI)
│   │   ├── aoe4world_stats.py       ← get_civ_stats, get_matchup_stats, get_map_stats
│   │   ├── aoe4world_players.py     ← search_player, get_player_profile, get_player_matches
│   │   ├── aoe4world_leaderboards.py← get_leaderboard
│   │   ├── aoe4world_esports.py     ← get_esports_leaderboard
│   │   ├── aoe4world_patches.py     ← get_patch_notes
│   │   ├── game_data.py             ← query_unit_stats, query_building_stats, query_technology, compare_units
│   │   ├── build_orders.py          ← search_build_orders (aoe4guides.com)
│   │   ├── liquipedia.py            ← search_liquipedia
│   │   ├── knowledge_base.py        ← search_pro_content (YouTube transcripts)
│   │   ├── ageups.py                ← get_ageup_stats
│   │   └── wiki.py                  ← EXISTE pero NO registrada (eliminada)
│   └── scripts/
│       ├── __init__.py
│       ├── scrape_youtube.py        ← Scraping de videos de YouTube con yt-dlp
│       ├── ingest_videos.py         ← Ingesta: Apify transcripts → chunks → embeddings → SQLite
│       └── update_knowledge.py      ← Update incremental de la knowledge base
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx
│       ├── globals.css
│       ├── components/
│       │   ├── ChatInterface.tsx     ← Componente principal del chat
│       │   ├── ChatMessage.tsx       ← Render de mensajes (markdown, tool indicators)
│       │   ├── ChatInput.tsx         ← Input de texto + boton enviar
│       │   ├── Header.tsx            ← Header con titulo
│       │   ├── SourceCitation.tsx    ← Citations: aoe4world (azul), youtube (rojo), etc.
│       │   ├── SuggestedQuestions.tsx ← Preguntas sugeridas basadas en respuesta
│       │   └── WelcomeScreen.tsx     ← Pantalla inicial con ejemplos
│       ├── hooks/
│       │   (vacio — useChat.ts esta en components/)
│       └── lib/
│           (vacio — types.ts esta en components/)
│       (NOTA: useChat.ts y types.ts estan en components/ no en hooks/ y lib/)
```

---

## Credenciales

- **OpenAI API Key:** En `backend/.env` como `OPENAI_API_KEY`
- **Apify API Token:** En `backend/.env` como `APIFY_API_TOKEN` (para transcripts YouTube)
- **Resto de APIs:** No necesitan key (AoE4 World, AoE4 Guides, Liquipedia son publicas)

---

## Costes

### Por consulta
- **GPT-4.1-mini:** ~$0.002-0.004 por query (input $0.40/1M tokens, output $1.60/1M tokens)
- **Embedding (search_pro_content):** ~$0.00002 por query
- **APIs externas:** $0 (todas gratuitas)
- **Total por query:** ~$0.003

### Overhead fijo por request
- System prompt: ~1,319 tokens
- 16 tool definitions: ~2,758 tokens
- Total fijo: ~4,077 tokens ($0.0016 por request solo de overhead)

### Estimacion mensual
| Escenario | Queries/dia | Coste OpenAI/mes | Infra/mes | Total/mes |
|-----------|-------------|------------------|-----------|-----------|
| Testing | 20 | ~$2 | $0 | ~$2 |
| 100 usuarios | 300 | ~$27 | $5 | ~$32 |
| 500 usuarios | 1500 | ~$135 | $10 | ~$145 |

### Coste one-time de ingesta
- Embeddings de 2,776 chunks: ~$0.05
- Apify transcripts de 208 videos: ~$1.04
- Total ingesta: ~$1.09

---

## Configuracion clave (config.py)

- **Modelo LLM:** `gpt-4.1-mini`
- **Max tool calls por turno:** 5
- **Rate limit API:** 20 requests/min por IP (slowapi)
- **Cache TTLs:** Stats 1h, Players 5min, Wiki 24h, Builds 1h, Liquipedia 1h
- **Liquipedia rate limit:** 2 segundos entre requests
- **22 civilizaciones** con aliases en espanol e ingles
- **Glosario de abreviaciones:** maa, xbow, fc, tc, bo, etc. → expansion automatica en queries del usuario

---

## Rate Limiting (backend)
- `slowapi` en `main.py`: 20 requests/minuto por IP en `/api/chat`
- Health endpoint sin limite
- Si se excede: HTTP 429

---

## Git / Deployment

### Estado actual
- **NO hay repositorio git inicializado** en la carpeta del proyecto
- **NO esta desplegado** en Railway ni en ningun servidor
- Anteriormente se menciono GitHub pero nunca se hizo push

### Para desplegar
1. Inicializar git: `cd aoe4-ragbot && git init`
2. Crear repo en GitHub
3. Primer commit y push
4. Desplegar backend en Railway (Python)
5. Desplegar frontend en Vercel
6. Actualizar CORS en `main.py` con URLs de produccion

### .gitignore actual
```
node_modules/
.env
__pycache__/
*.pyc
backend/data/cache/
backend/data/knowledge.db
backend/data/video_candidates.json
backend/data/transcript_cache.json
.venv/
.next/
out/
```

---

## Modelo de Negocio (en discusion)

### Decision actual: Academia Discord + Web complementaria

**Concepto:** "AoE4 Academy" — servidor privado de Discord con Vortix como pro player residente, bot IA integrado, y web con herramientas interactivas.

### Estructura propuesta
```
WEB (aoetest.vercel.app) — herramientas interactivas
  FREE: Quiz, explorador de civs, ruleta, chatbot limitado (5/dia)
  PREMIUM: Chatbot ilimitado, build order editor, economy simulator, replay analyzer

DISCORD — comunidad + chatbot + coaching
  FREE: Canal general, bot 5 preguntas/dia
  MEMBER (4.99€/mes): Bot ilimitado, canales de estrategia
  PRO (9.99€/mes): Coaching grupales, replay reviews
  VIP (24.99€/mes): Sesion privada mensual con Vortix
```

### Plataforma de pagos
- **Whop.com** (recomendado para empezar) — 3% comision, vincula roles de Discord automaticamente
- **Discord Server Subscriptions** (cuando tengamos 500+ miembros) — 0% comision
- **Patreon** (alternativa) — 8-12% comision

### Consideraciones legales
- **Microsoft Game Content Usage Rules:** "Personal, noncommercial use" para assets del juego. PERO toda la comunidad AoE4 (Hera con Patreon $1-$100/mes, AoE4 World con Ko-fi, Overwolf overlays de pago) usa assets del juego y monetiza. Microsoft no ha perseguido a nadie.
- **Lo que vendemos NO son datos de Microsoft** — vendemos coaching, comunidad, y acceso a un pro player. Las tools son un complemento.
- **Atribucion:** Poner "Stats powered by aoe4world.com" en el footer de la web.
- **Disclaimer:** "Not affiliated with Microsoft or Relic Entertainment"
- **Iconos del juego:** Los usamos en la web. Toda la comunidad lo hace. Riesgo teorico, riesgo real nulo. Plan B: reemplazar por iconos propios si algun dia lo piden.

### Bot de Discord (pendiente de implementar)
- `discord.py` — se conecta al mismo backend
- Comandos: `/ask`, `/stats`, `/build`, `/matchup`, `/player`, etc.
- Control de acceso por rol (free/member/pro)
- Soporta DMs (chat privado con el bot)
- Mismas 16 tools, mismo coste por query
- ~200 lineas de codigo nuevo
- **Requisito:** Crear aplicacion en Discord Developer Portal y obtener Bot Token

### Numeros de rentabilidad
```
Escenario: 100 free + 20 members + 5 pro
  Coste OpenAI: ~$67.50/mes
  Ingresos: 20×4.99€ + 5×9.99€ = ~$150€/mes
  Beneficio: ~$80€/mes
```

---

## Pendiente (Fase 3)

### Alta prioridad
1. **Guias principales de Vortix** — Contenido exclusivo escrito/validado por Vortix. Seran "las mas importantes" para las respuestas del bot. Aun NO se han creado ni ingested.
2. **Bot de Discord** — Crear aplicacion en Discord Developer Portal, escribir discord_bot.py, conectar al backend.
3. **Git + Deploy** — Inicializar repo, push a GitHub, deploy backend (Railway) + frontend (Vercel).

### Media prioridad
4. **Sistema de autenticacion** — Discord OAuth para la web, unificar identidad web + Discord.
5. **Sistema de limites** — Tabla SQLite `usage(user_id, month, count)`, limites por tier.
6. **Whop.com** — Crear cuenta, vincular servidor Discord, configurar tiers.
7. **Mas canales de YouTube** — Considerar anadir Drongo, Spirit of the Law, T90 (AoE2 pero relevante).

### Baja prioridad
8. **Replay analyzer** — Herramienta web para analizar replays (proyecto separado mencionado por el usuario).
9. **Historial en localStorage** — Guardar ultimos 50 mensajes en el frontend.
10. **Mejorar patch notes tool** — Actualmente solo muestra version, no notas detalladas.

---

## Problemas conocidos y soluciones

### YouTube IP rate limiting
- **Problema:** youtube-transcript-api descarga transcripts directo de YouTube. Tras ~25 descargas rapidas, YouTube bloquea la IP con 429 errors.
- **Solucion:** Usar Apify (actor karamelo~youtube-transcripts) que usa proxies. $0.005/video. Transcripts se cachean localmente.

### Puerto 8000 ocupado por MediaPulse
- **Problema:** El proyecto MediaPulse (agentradar) tambien usa puerto 8000. Si se arranca antes, el AoE4 bot no puede arrancar.
- **Solucion:** Verificar con `curl http://localhost:8000/api/health`. Si devuelve `{"detail":"Not authenticated"}` es MediaPulse. Matar ese proceso.

### Bot inventa datos del juego
- **Problema:** GPT-4.1-mini a veces inventa mecanicas del juego (ej: "archers counter knights").
- **Solucion:** CRITICAL RULE en el system prompt que obliga a verificar con tools antes de hacer claims.

### Vortix no aparece en busquedas
- **Problema:** Queries en ingles devolvian contenido de Beastyqt/Valdemar en vez de Vortix (que esta en espanol).
- **Solucion:** System prompt instruye pasar `channel="Vortix"` cuando el usuario menciona Vortix.

### Python 3.14 incompatible con ChromaDB
- **Problema:** ChromaDB no soporta Python 3.14 (depende de hnswlib que no compila).
- **Solucion:** Se reemplazo ChromaDB por SQLite + numpy. Mismo resultado, sin dependencias problematicas.

---

## Historial de cambios

### Fase 1 (completada)
- Backend FastAPI con 16 tools (incluyendo wiki)
- Frontend Next.js con chat streaming
- 5 APIs gratuitas conectadas
- System prompt basico
- Cache en memoria
- CORS configurado

### Fase 2 (completada — 19 Febrero 2026)
- Knowledge base con SQLite + numpy (reemplazo de ChromaDB)
- Ingesta de 208 videos de YouTube (2,776 chunks) via Apify
- 4 canales: Beastyqt, Valdemar, Vortix, MarineLorD
- Tool `search_pro_content` para buscar contenido de pros
- Tool `get_patch_notes` para info de patches
- Tool `get_ageup_stats` para timings de age-up
- Eliminacion de wiki tools (search_wiki, get_wiki_page) por mediocres
- System prompt reescrito con CRITICAL RULE, prioridades, y manejo de ambiguedad
- Rate limiting con slowapi (20/min)
- SSE event `tool_call` para mostrar que tool se usa en el frontend
- Glosario de abreviaciones gaming (glossary.py)
- Scripts de scraping, ingesta y update de knowledge base

### QA Testing (20 Febrero 2026)
14 rounds de testing automatizado (~65 queries), 13 bugs encontrados y corregidos:

**Bugs de game_store.py (formato de datos):**
1. `format_unit()` no mostraba bonus damage (modifiers array ignorado) → Anadido parseo de modifiers con "Bonus vs [class]: +[value]"
2. `format_building()` incompleto: faltaba garrison, armor, weapons, sight → Anadidos los 4 campos
3. `format_technology()` no mostraba building de investigacion → Anadido campo producedBy
4. `_resolve_name()` no normalizaba underscores ("town_center" no matcheaba "town center") → Anadido .replace("_", " ")
5. Busqueda por nombre no encontraba unidades navales (Atakebune, Junk) al buscar "ship" → Anadida busqueda por displayClasses cuando hay pocos resultados por nombre
6. Springald no mostraba rol anti-siege (API no incluye bonus vs siege) → Anadido diccionario UNIT_EXTRA_INFO con info suplementaria de roles/counters
7. Keep no explicaba mecanica de garrison damage → Anadida nota "Garrisoned units add extra arrows" + BUILDING_EXTRA_INFO dict

**Bugs de aoe4world_stats.py (map stats):**
8. `get_map_stats()` devolvia JSON crudo truncado → Reescrito con formateo markdown (tabla de civs por win rate)
9. Key del nombre de mapa era "map" no "name" en el API → Corregido para buscar ambas keys
10. Win rates del API ya vienen en porcentaje (53.8), no fraccion (0.53) → Corregida logica de formateo

**Bugs de tools/definitions.py:**
11. Modo `rm_team` no existe en el API (devuelve 404) → Reemplazado por rm_2v2/rm_3v3/rm_4v4 en todos los enums

**Bugs de aoe4world_players.py:**
12. Player matches: API wraps players en {"player": {...}} pero codigo accedia directo → Fix con entry.get("player", entry)

**Bugs de chat.py (system prompt):**
13. Bot no reconocia civs que NO estan en AoE4 (Aztecs) → Anadida lista de 22 civs + instruccion de rechazar non-AoE4
- Anadidas secciones: Counter Relationships, Civ Passive Bonuses, meta multi-tool instruction

**Resultado final:** 3 rondas consecutivas 100% PASS (Rounds 12-14). Bot nunca inventa datos, selecciona tools correctas, combina hasta 5 tools por query, maneja espanol/ingles, abreviaciones, typos, civs invalidas, prompt injection.
