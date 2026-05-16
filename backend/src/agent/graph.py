from deepagents import create_deep_agent

from agent.models.llm import llm

graph = create_deep_agent(
    model=llm,
    system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
)

__all__ = ["graph"]