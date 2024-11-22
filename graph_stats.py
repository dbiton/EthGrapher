import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

def graph_average_degree(graph):
    try:
        num_edges = graph.number_of_edges()
        num_nodes = graph.number_of_nodes()
        if num_nodes == 0:
            return 0.0  # Avoid division by zero if there are no nodes
        avg_degree = (2 * num_edges) / num_nodes
        return avg_degree
    except Exception as e:
        print(f"Exception in graph_average_degree: {e}")
        return float('nan')

def graph_cluster_coe(graph):
    try:
        return nx.average_clustering(graph)
    except Exception as e:
        print(f"Exception in graph_cluster_coe: {e}")
        return float('nan')

def graph_coloring(graph):
    try:
        coloring = nx.coloring.greedy_color(graph)
        return len(set(coloring.values()))
    except Exception as e:
        print(f"Exception in graph_coloring: {e}")
        return float('nan')

def graph_transitivity(graph):
    try:
        return nx.transitivity(graph)
    except Exception as e:
        print(f"Exception in graph_transitivity: {e}")
        return float('nan')

def graph_assortativity(graph):
    try:
        return nx.degree_assortativity_coefficient(graph)
    except Exception as e:
        print(f"Exception in graph_assortativity: {e}")
        return float('nan')

def graph_modularity(G):
    try:
        communities = list(greedy_modularity_communities(G))
        return nx.algorithms.community.modularity(G, communities)
    except Exception as e:
        print(f"Exception in graph_modularity: {e}")
        return float('nan')

def graph_density(graph):
    try:
        return nx.density(graph)
    except Exception as e:
        print(f"Exception in graph_density: {e}")
        return float('nan')

def graph_diameter(G):
    try:
        if nx.is_connected(G):
            diameter = nx.diameter(G)
        else:
            diameter = max(
                nx.diameter(G.subgraph(comp)) for comp in nx.connected_components(G)
            )
        return diameter
    except Exception as e:
        print(f"Exception in graph_diameter: {e}")
        return float('nan')

def graph_conflict_percentage(G):
    try:
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        max_possible_edges = num_nodes * (num_nodes - 1) / 2
        percentage_conflicts = (num_edges / max_possible_edges) * 100 if max_possible_edges > 0 else 0
        return percentage_conflicts
    except Exception as e:
        print(f"Exception in graph_conflict_percentage: {e}")
        return float('nan')
