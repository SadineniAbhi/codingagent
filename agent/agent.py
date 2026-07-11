from pydantic import SecretStr
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.pregel.main import BaseCheckpointSaver
from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph

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


def build_graph(checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
    return create_react_agent(
        model=model,
        tools=[bash],
        prompt=_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
