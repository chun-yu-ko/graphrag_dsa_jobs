import os
import asyncio
import tiktoken
import pandas as pd
from app.utils import logger
from app.settings import INPUT_DIR, LANCEDB_URI, API_KEY, API_BASE
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import store_entity_semantic_embeddings
from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.query.structured_search.global_search.community_context import GlobalCommunityContext
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore

async def setup_llm_and_embedder():
    logger.info("Setting up LLM and embedder")
    llm = ChatOpenAI(api_key=API_KEY, api_base=API_BASE, model="gpt-4o-mini", api_type=OpenaiApiType.OpenAI, max_retries=5)
    token_encoder = tiktoken.get_encoding("cl100k_base")
    text_embedder = OpenAIEmbedding(api_key=API_KEY, api_base=API_BASE, api_type=OpenaiApiType.OpenAI, model="text-embedding-3-small", max_retries=20)
    logger.info("LLM and embedder setup complete")
    return llm, token_encoder, text_embedder

async def load_context():
    logger.info("Loading context data")
    try:
        entity_df = pd.read_parquet(f"{INPUT_DIR}/create_final_nodes.parquet")
        entity_embedding_df = pd.read_parquet(f"{INPUT_DIR}/create_final_entities.parquet")
        entities = read_indexer_entities(entity_df, entity_embedding_df, 2)

        description_embedding_store = LanceDBVectorStore(collection_name="entity_description_embeddings")
        description_embedding_store.connect(db_uri=LANCEDB_URI)
        store_entity_semantic_embeddings(entities=entities, vectorstore=description_embedding_store)

        relationship_df = pd.read_parquet(f"{INPUT_DIR}/create_final_relationships.parquet")
        relationships = read_indexer_relationships(relationship_df)

        report_df = pd.read_parquet(f"{INPUT_DIR}/create_final_community_reports.parquet")
        reports = read_indexer_reports(report_df, entity_df, 2)

        text_unit_df = pd.read_parquet(f"{INPUT_DIR}/create_final_text_units.parquet")
        text_units = read_indexer_text_units(text_unit_df)

        covariate_df = pd.read_parquet(f"{INPUT_DIR}/create_final_covariates.parquet")
        claims = read_indexer_covariates(covariate_df)

        logger.info(f"Number of claims: {len(claims)}")
        covariates = {"claims": claims}

        logger.info("Context data loaded")
        return entities, relationships, reports, text_units, description_embedding_store, covariates
    except Exception as e:
        logger.error(f"Error loading context data: {str(e)}")
        raise

async def setup_search_engines(llm, token_encoder, text_embedder, entities, relationships, reports, text_units, description_embedding_store, covariates):
    logger.info("Setting up search engines")

    local_context_builder = LocalSearchMixedContext(
        community_reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        covariates=covariates,
        entity_text_embeddings=description_embedding_store,
        embedding_vectorstore_key=EntityVectorStoreKey.ID,
        text_embedder=text_embedder,
        token_encoder=token_encoder,
    )

    local_search_engine = LocalSearch(
        llm=llm,
        context_builder=local_context_builder,
        token_encoder=token_encoder,
        llm_params={"max_tokens": 2_000, "temperature": 0.0},
        context_builder_params={
            "text_unit_prop": 0.5,
            "community_prop": 0.1,
            "conversation_history_max_turns": 5,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": 10,
            "top_k_relationships": 10,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,
            "max_tokens": 12_000,
        },
        response_type="multiple paragraphs",
    )

    global_context_builder = GlobalCommunityContext(
        community_reports=reports,
        entities=entities,
        token_encoder=token_encoder,
    )

    global_search_engine = GlobalSearch(
        llm=llm,
        context_builder=global_context_builder,
        token_encoder=token_encoder,
        max_data_tokens=12_000,
        map_llm_params={"max_tokens": 1000, "temperature": 0.0, "response_format": {"type": "json_object"}},
        reduce_llm_params={"max_tokens": 2000, "temperature": 0.0},
        allow_general_knowledge=False,
        json_mode=True,
        context_builder_params={
            "use_community_summary": False,
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": 12_000,
            "context_name": "Reports",
        },
        concurrent_coroutines=32,
        response_type="multiple paragraphs",
    )

    logger.info("Search engines setup complete")
    return local_search_engine, global_search_engine
