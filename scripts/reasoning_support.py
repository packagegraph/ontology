"""OWL-RL diagnostics for fixture-based reasoning checks, not DL certification."""

from rdflib import Graph, URIRef
from owlrl import DeductiveClosure, OWLRL_Semantics

OWL_RL_ERROR = URIRef("http://www.daml.org/2002/03/agents/agent-ont#error")


def owlrl_errors(graph: Graph) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in graph.objects(None, OWL_RL_ERROR)}))


def expand_checked(graph: Graph) -> Graph:
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    messages = owlrl_errors(graph)
    if messages:
        raise AssertionError("OWL-RL reported errors:\n" + "\n".join(messages))
    return graph
