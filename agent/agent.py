import subprocess
from typing import Annotated, NotRequired
from langgraph.pregel.main import BaseCheckpointSaver
from typing_extensions import TypedDict

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from pydantic import SecretStr
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from service.bash_service import run_command
from utils.env import settings


with open("agent/system_prompt.md") as f:
    _SYSTEM_PROMPT = f.read()

model = ChatAnthropic(
    model_name="claude-opus-4-7",
    api_key=SecretStr(settings.ANTHROPIC_API_KEY),
    timeout=None,
    stop=None,
)


Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)

langfuse_handler = CallbackHandler()


@tool
def bash(command: str) -> str:
    """Execute a bash command and return its output."""
    result = run_command(command)
    output = result.stdout
    if result.stderr:
        output += f"\nstderr: {result.stderr}"
    if result.returncode != 0:
        output += f"\nexit code: {result.returncode}"
    return output or "(no output)"


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_task: NotRequired[str]
    diff: NotRequired[str]
    approved: NotRequired[bool]



def snapshot(state: State) -> dict:
    subprocess.run(
        f"rsync -a --exclude='.git' /tmp/workspace/ /tmp/snapshot/", shell=True
    )
    return {}

def generate_code(state: State) -> dict:
    agent = create_agent(model, tools=[bash], system_prompt=_SYSTEM_PROMPT)
    messages = state.get("messages", [])
    messages.append(HumanMessage(content=state.get('user_task', '')))
    result = agent.invoke({"messages": messages}, config={"callbacks": [langfuse_handler]}) # type: ignore
    summary = result["messages"][-1].content
    return {"messages": [AIMessage(content= summary)]}


def get_diff(state: State) -> dict:
    result = run_command("diff -ru --exclude='.git' --exclude='.venv' /tmp/snapshot /tmp/workspace")
    return {"diff": result.stdout}


def human_review(state: State) -> dict:
    if not state.get("diff", "").strip():
        return {"approved": True}

    answer = interrupt({
        "question": "Approve changes? (yes/no)",
        "diff": state.get("diff", ""),
    })

    approved = str(answer).strip().lower() in ("yes", "y")
    return {"approved": approved}


def revert(state: State) -> dict:
    run_command("rsync -a --exclude='.git' /tmp/snapshot/ /tmp/workspace/")
    return {"messages": [AIMessage(content="Changes reverted to snapshot.")]}


def route_after_review(state: State) -> str:
    return END if state.get("approved") else "revert"


def build_graph(checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
    g = StateGraph(State)

    g.add_node("snapshot", snapshot)
    g.add_node("generate_code", generate_code)
    g.add_node("get_diff", get_diff)
    g.add_node("human_review", human_review)
    g.add_node("revert", revert)

    g.set_entry_point("snapshot")
    g.add_edge("snapshot", "generate_code")
    g.add_edge("generate_code", "get_diff")
    g.add_edge("get_diff", "human_review")
    g.add_conditional_edges(
        "human_review",
        route_after_review,
        {"revert": "revert", END: END},
    )
    g.add_edge("revert", END)

    return g.compile(checkpointer=checkpointer)

