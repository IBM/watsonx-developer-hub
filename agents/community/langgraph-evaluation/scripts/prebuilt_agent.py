from langgraph_react_agent_base.agent import get_graph_closure


def make_agent(client, model_id, system_propt=None):

    graph = get_graph_closure(client, model_id)
    if system_propt:
        agent = graph(system_propt)
    else:
        agent = graph()
    return agent