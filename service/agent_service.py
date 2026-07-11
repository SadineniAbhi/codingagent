import json
from payloads.agent import Execute
from utils.logger import get_logger
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from utils.custom_errors import APIError, ThreadNotFound, FailedToGetState


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


class AgentService:
    def __init__(self, graph: CompiledStateGraph) -> None:
        self.logger = get_logger(__name__)
        self.graph = graph

    async def s_run(self, thread_id: str, task: Execute) -> StreamingResponse:
        self.logger.info("Starting run for thread %s", thread_id)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        messages = {"messages": [("user", task.task)]}

        async def generate():
            try:
                async for chunk, metadata in self.graph.astream(messages, config=config, stream_mode="messages"):
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        yield _sse({"type": "token", "content": chunk.content, "node": metadata.get("langgraph_node")})
            except Exception:
                self.logger.exception("Stream failed for thread %s", thread_id)
                yield _sse({"type": "error", "message": "An unexpected error occurred"})

        return StreamingResponse(generate(), media_type="text/event-stream")

    async def s_get_state(self, thread_id: str) -> dict:
        try:
            self.logger.info("Fetching state for thread %s", thread_id)
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
            state = await self.graph.aget_state(config)
            if not state.values:
                raise ThreadNotFound("Thread not found", 404)
            return {"messages": state.values["messages"]}
        except APIError:
            raise
        except Exception as e:
            raise FailedToGetState("Failed to get state", 500) from e
