from langgraph.graph.state import CompiledStateGraph

from agent import graph


def test_graph_type():
    assert isinstance(graph, CompiledStateGraph)


def test_graph_import():
    from agent import graph as g

    assert g is graph