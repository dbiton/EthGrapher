import networkx as nx


def graph_average_degree(graph):
    num_edges = graph.number_of_edges()
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return 0.0  # Avoid division by zero if there are no nodes
    avg_degree = (2 * num_edges) / num_nodes
    return avg_degree


def graph_cluster_coe(graph):
    return nx.average_clustering(graph)

def graph_coloring(graph):
    coloring = nx.coloring.greedy_color(graph)
    return len(set(coloring.values()))

def graph_transitivity(graph):
    return nx.transitivity(graph)


def graph_assortativity(graph):
    return nx.degree_assortativity_coefficient(graph)


from networkx.algorithms.community import greedy_modularity_communities


def graph_modularity(G):
    communities = list(greedy_modularity_communities(G))
    return nx.algorithms.community.modularity(G, communities)


def graph_density(graph):
    return nx.density(graph)


def graph_diameter(G):
    if nx.is_connected(G):
        diameter = nx.diameter(G)
    else:
        diameter = max(
            nx.diameter(G.subgraph(comp)) for comp in nx.connected_components(G)
        )
    return diameter


def graph_edge_connectivity(G):
    return nx.edge_connectivity(G)