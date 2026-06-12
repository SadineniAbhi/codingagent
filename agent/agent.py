import os
import subprocess
from typing import Annotated, NotRequired
from typing_extensions import TypedDict

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from pydantic import SecretStr
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from service.bash_service import run_command
from env import settings



with open("agent/system_prompt.md") as f:
    _SYSTEM_PROMPT = f.read()

model = ChatAnthropic(
    model_name="claude-opus-4-7",
    api_key=SecretStr(settings.ANTHROPIC_API_KEY),
    timeout=None,
    stop=None,
)

checkpointer = MemorySaver()


PAT_TOKEN = settings.PAT_TOKEN
REPO_URL = settings.REPO_URL
REPO_NAME = REPO_URL.rstrip("/").split("/")[-1].removesuffix(".git")



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


def clone_repo(repo_url: str, pat_token: str) -> bool:
    os.makedirs("/tmp/workspace", exist_ok=True)
    url_with_token = repo_url.replace("https://", f"https://x:{pat_token}@")
    subprocess.run(f"git clone {url_with_token}", shell=True, cwd="/tmp/workspace")
    return True


def snapshot(state: State) -> dict:
    subprocess.run(
        f"rsync -a --exclude='.git' /tmp/workspace/{REPO_NAME}/ /tmp/snapshot/", shell=True
    )
    return {}




def generate_code(state: State) -> dict:
    agent = create_agent(model, tools=[bash])
    result = agent.invoke({
        "messages": [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"Task: {state.get('user_task', '')}"),
        ]
    })
    summary = result["messages"][-1].content
    return {"messages": [AIMessage(content=f"Code generation complete: {summary}")]}


def get_diff(state: State) -> dict:
    result = subprocess.run(
        "diff -ru --exclude='.git' --exclude='.venv' /tmp/snapshot /tmp/workspace/to-do",
        shell=True, text=True, capture_output=True,
    )
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
    subprocess.run("rsync -a --exclude='.git' /tmp/snapshot/ /tmp/workspace/to-do/", shell=True)
    return {"messages": [AIMessage(content="Changes reverted to snapshot.")]}


def route_after_review(state: State) -> str:
    return END if state.get("approved") else "revert"


def build_graph() -> CompiledStateGraph:
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



