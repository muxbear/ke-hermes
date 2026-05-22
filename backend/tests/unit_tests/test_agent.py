from agent import get_graph, init_graph, shutdown_graph


def test_graph_type():
    """Verify graph module exports are callable."""
    assert callable(get_graph)
    assert callable(init_graph)
    assert callable(shutdown_graph)


def test_graph_import():
    """Verify graph exports are consistent on re-import."""
    from agent import get_graph as g

    assert g is get_graph