import asyncio
import pandas as pd
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.handlers import chat_completions, list_models
from app.utils import logger
from app.settings import INPUT_DIR, LANCEDB_URI, PORT
from app.setup import setup_llm_and_embedder, load_context, setup_search_engines
from app.models import ChatCompletionRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    global local_search_engine, global_search_engine
    try:
        logger.info("Initializing search engines...")
        llm, token_encoder, text_embedder = await setup_llm_and_embedder()
        entities, relationships, reports, text_units, description_embedding_store, covariates = await load_context()
        local_search_engine, global_search_engine = await setup_search_engines(
            llm, token_encoder, text_embedder, entities, relationships, reports, text_units, description_embedding_store, covariates
        )
        logger.info("Initialization complete.")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

    yield

    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.post("/v1/chat/completions")
async def chat_completions_endpoint(request: ChatCompletionRequest):
    return await chat_completions(request, local_search_engine, global_search_engine)

@app.get("/v1/models")
async def list_models_endpoint():
    return await list_models()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
