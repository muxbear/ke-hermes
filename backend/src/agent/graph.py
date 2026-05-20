from deepagents import create_deep_agent

from agent.models.llm import llm
from agent.tools.internet_search import internet_search
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

graph = create_deep_agent(
    model=llm,
    tools=[internet_search],
    checkpointer=checkpointer,    
    system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
)

__all__ = ["graph"]