import asyncio
import json
import uuid
import time
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import HTTPException
from app.models import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionResponseChoice, Message, Usage
from app.utils import format_response, logger
from app.settings import API_KEY, API_BASE, MODEL_NAME_GLOBAL_SEARCH, MODEL_NAME_LOCAL_SEARCH

async def chat_completions(request: ChatCompletionRequest, local_search_engine, global_search_engine):
    if not local_search_engine or not global_search_engine:
        logger.error("Search engines not initialized")
        raise HTTPException(status_code=500, detail="Search engines not initialized")

    try:
        logger.info(f"Received chat completion request: {request}")
        prompt = request.messages[-1].content

        if request.model == MODEL_NAME_GLOBAL_SEARCH:
            result = await global_search_engine.asearch(prompt)
        else:
            result = await local_search_engine.asearch(prompt)
        
        formatted_response = format_response(result.response)
        logger.info(f"Formatted search result: {formatted_response}")

        if request.stream:
            async def generate_stream():
                chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
                lines = formatted_response.split('\n')
                for i, line in enumerate(lines):
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": line + '\n'}, "finish_reason": None}]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    await asyncio.sleep(0.05)

                final_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate_stream(), media_type="text/event-stream")
        else:
            response = ChatCompletionResponse(
                model=request.model,
                choices=[ChatCompletionResponseChoice(index=0, message=Message(role="assistant", content=formatted_response), finish_reason="stop")],
                usage=Usage(prompt_tokens=len(prompt.split()), completion_tokens=len(formatted_response.split()), total_tokens=len(prompt.split()) + len(formatted_response.split()))
            )
            logger.info(f"Sending response: {response}")
            return JSONResponse(content=response.dict())

    except Exception as e:
        logger.error(f"Error processing chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def list_models():
    logger.info("Received model list request")
    current_time = int(time.time())
    models = [
        {"id": MODEL_NAME_GLOBAL_SEARCH, "object": "model", "created": current_time, "owned_by": "ko"},
        {"id": MODEL_NAME_LOCAL_SEARCH, "object": "model", "created": current_time, "owned_by": "ko"}
    ]

    response = {"object": "list", "data": models}
    logger.info(f"Sending model list: {response}")
    return JSONResponse(content=response)
