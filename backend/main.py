"""FastAPI application entry point."""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sse_starlette.sse import EventSourceResponse

from models import ChatRequest
from chat import chat_stream
from data.loader import load_all
from data import game_store
from utils import close_session

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load game data
    print("[startup] Loading game data...")
    data = await load_all()
    game_store.store = game_store.GameStore(data)

    # Startup: initialize knowledge base
    print("[startup] Loading knowledge base...")
    try:
        import knowledge
        kb_count = knowledge.count()
        print(f"[startup] Knowledge base: {kb_count} chunks loaded")
    except Exception as e:
        print(f"[startup] Knowledge base unavailable: {e}")

    print("[startup] Ready!")
    yield
    # Shutdown: close HTTP session
    await close_session()
    print("[shutdown] Closed.")


app = FastAPI(
    title="AoE4 RAGBot API",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    from data.game_store import store
    kb_chunks = 0
    try:
        import knowledge
        kb_chunks = knowledge.count()
    except Exception:
        pass
    return {
        "status": "ok",
        "game_data_loaded": store is not None,
        "units": len(store.units) if store else 0,
        "buildings": len(store.buildings) if store else 0,
        "technologies": len(store.technologies) if store else 0,
        "knowledge_base_chunks": kb_chunks,
    }


@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    async def event_generator():
        async for chunk in chat_stream(chat_request):
            yield json.dumps(chunk)

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
