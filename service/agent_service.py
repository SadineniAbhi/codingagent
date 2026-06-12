import json
from langgraph.types import Command
from payloads.agent import Execute
from utils.custom_errors import APIError, FailedToStream, GraphNotPaused, FailedToResume, ThreadNotFound, FailedToGetState
from utils.logger import get_logger
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig

logger = get_logger(__name__)

def _sse(data: dict) -> str:
    """
        This method is used for sse formating of the data 
    """
    return f"data: {json.dumps(data)}\n\n"


def _serialize(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj



async def _stream_graph(graph, input_or_command, config: RunnableConfig):
    async for chunk in graph.astream(input_or_command, config=config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            if node_name == "__interrupt__":
                yield _sse({"type": "interrupted", "message": node_output[0].value})
            else:
                yield _sse({"type": "node_update", "node": node_name, "output": _serialize(node_output)})


async def s_run(thread_id: str, task: Execute, graph):
    try:
        logger.info("Starting run for thread %s", thread_id)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        async def generate():
            async for line in _stream_graph(graph, {"messages": [], "user_task": task.task}, config):
                yield line

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception:
        logger.exception("Failed to stream graph for thread %s", thread_id)
        raise FailedToStream("unable stream the response", 500)


async def s_resume(thread_id: str, input: str, graph):
    try:
        logger.info("Resuming graph for thread %s", thread_id)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)
        if not state.next:
            raise GraphNotPaused("Graph is not paused", 400)

        async def generate():
            async for line in _stream_graph(graph, Command(resume=input), config):
                yield line

        return StreamingResponse(generate(), media_type="text/event-stream")
    except APIError:
        logger.exception("APIError during resume for thread %s", thread_id)
        raise
    except Exception:
        logger.exception("Failed to resume graph for thread %s", thread_id)
        raise FailedToResume("Failed to resume graph", 500)


async def s_get_state(thread_id: str, graph):
    try:
        logger.info("Fetching state for thread %s", thread_id)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)
        if not state.values:
            raise ThreadNotFound("Thread not found", 404)
        return {"messages": state.values["messages"], "paused_at": list(state.next)}
    except APIError:
        logger.exception("APIError during get_state for thread %s", thread_id)
        raise
    except Exception:
        logger.exception("Failed to get state for thread %s", thread_id)
        raise FailedToGetState("Failed to get state", 500)

