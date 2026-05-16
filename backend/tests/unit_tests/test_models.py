from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from agent.models import embeddings, llm


def test_llm_instance():
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "deepseek-v4-pro"


def test_embeddings_instance():
    assert isinstance(embeddings, OpenAIEmbeddings)


def test_model_exports():
    from agent.models import embeddings as em
    from agent.models import llm as lm

    assert isinstance(lm, ChatOpenAI)
    assert isinstance(em, OpenAIEmbeddings)