import os
import subprocess
from typing import Annotated, NotRequired

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langchain.agents import create_agent
from pydantic import SecretStr
from typing_extensions import TypedDict

PAT_TOKEN = "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"
REPO_URL = "https://github.com/SadineniAbhi/to-do.git"

model = ChatAnthropic(
    model_name="claude-opus-4-7",
    api_key=SecretStr(os.environ.get("ANTHROPIC_API_KEY", "")),
    timeout=None,
    stop=None,
)


REPO_DIR = REPO_URL.rstrip("/").split("/")[-1].removesuffix(".git")

def run_command(command: str) -> str:
    os.makedirs("/tmp/workspace", exist_ok=True)
    result = subprocess.run(command, shell=True, text=True, capture_output=True, cwd=f"/tmp/workspace/{REPO_DIR}")
    output = result.stdout
    if result.stderr:
        output += f"\nstderr: {result.stderr}"
    if result.returncode != 0:
        output += f"\nexit code: {result.returncode}"
    return output or "(no output)"


@tool
def bash(command: str) -> str:
    """Execute a bash command and return its output."""
    return run_command(command)



class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_task: NotRequired[str]
    diff: NotRequired[str]
    approved: NotRequired[bool]


def get_user_input(state: State) -> dict:
    user_task = input("What do you want to do? ").strip()
    return {"user_task": user_task}


def clone_repo(state: State) -> dict:
    url_with_token = state.get("repo_url", "").replace("https://", f"https://x:{PAT_TOKEN}@")
    output = run_command(f"git clone {url_with_token}")
    return {}



def generate_code(state: State) -> dict:
    agent = create_agent(model, tools=[bash])
    result = agent.invoke({
        "messages": [
            SystemMessage(content=(
                "You are a coding agent. You have access to a bash tool to read, create, and edit files. "
                "The repository has been cloned into /tmp/workspace. "
                "The environment has Python, git, tree-sitter, and pyright pre-installed — use them freely via bash. "
                "Use tree-sitter to parse and understand code structure when needed. "
                "Run pyright to check for type errors after making changes and fix any issues before finishing. "
                "Use bash to navigate the repo, implement the required changes exactly as described in the plan, then stop. "
                "Do not ask for confirmation — just make the changes."
            )),
            HumanMessage(content=f"Task: {state.get('user_task', '')}"),
        ]
    })
    agent_summary = result["messages"][-1].content
    print(f"\nCode generation complete: {agent_summary[:200]}\n")
    return {}


def snapshot(state: State) -> dict:
    subprocess.run("rm -rf /tmp/snapshot && cp -r /tmp/workspace/to-do /tmp/snapshot", shell=True)
    return {}


def get_diff(state: State) -> dict:
    result = subprocess.run(
        "diff -ru --exclude='.git' --exclude='.venv' /tmp/snapshot /tmp/workspace/to-do",
        shell=True, text=True, capture_output=True
    )
    return {"diff": result.stdout}


def human_review(state: State) -> dict:
    if not state.get("diff", "").strip():
        return {}

    print("\n" + "=" * 60)
    print("DIFF:")
    print("=" * 60)
    print(state.get("diff", ""))
    print("=" * 60 + "\n")

    while True:
        answer = input("Approve changes? [yes/no]: ").strip().lower()
        if answer in ("yes", "y"):
            return {"approved": True}
        if answer in ("no", "n"):
            return {"approved": False}
        print("Please enter yes or no.")


def revert(state: State) -> dict:
    subprocess.run("cp -r /tmp/snapshot/. /tmp/workspace/to-do", shell=True)
    print("Reverted to snapshot")
    return {}



def route_after_review(state: State) -> str:
    if not state.get("diff", "").strip() or state.get("approved"):
        return "get_user_input"
    return "revert"


def build_graph() -> CompiledStateGraph[State, None, State, State]:
    graph = StateGraph(State)

    graph.add_node("get_user_input", get_user_input)
    graph.add_node("snapshot", snapshot)
    graph.add_node("generate_code", generate_code)
    graph.add_node("get_diff", get_diff)
    graph.add_node("human_review", human_review)
    graph.add_node("revert", revert)

    graph.set_entry_point("get_user_input")
    graph.add_edge("get_user_input", "snapshot")
    graph.add_edge("snapshot", "generate_code")
    graph.add_edge("generate_code", "get_diff")
    graph.add_edge("get_diff", "human_review")

    graph.add_conditional_edges(
        "human_review",
        route_after_review,
        {"revert": "revert", "get_user_input": "get_user_input"},
    )

    graph.add_edge("revert", "get_user_input")

    return graph.compile()



def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set")

    app = build_graph()
    app.invoke({"messages": []})


if __name__ == "__main__":
    main()
