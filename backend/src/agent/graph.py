from deepagents import create_deep_agent

from agent.models.llm import llm
from agent.tools.internet_search import internet_search

graph = create_deep_agent(
    model=llm,
    tools=[internet_search],    
    system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
)

__all__ = ["graph"]