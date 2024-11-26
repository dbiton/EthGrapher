from itertools import permutations
import random
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

def graph_greedy_coloring(graph):
    try:
        coloring = nx.coloring.greedy_color(graph, strategy="DSATUR")
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


def graph_longest_path_length(G):
    try:
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        longest_path_length = 0
        for comp_nodes in components:
            comp_size = len(comp_nodes)
            if comp_size <= longest_path_length:
                break
            sampled_nodes = random.sample(list(comp_nodes), min(1, comp_size // 10))
            for source_node in sampled_nodes:
                seen_nodes = {source_node}
                curr_node = source_node
                path_length = 1
                while True:
                    neighbors = set(G.neighbors(curr_node))
                    unseen_neighbors = list(neighbors.difference(seen_nodes))
                    if len(unseen_neighbors) == 0:
                        break
                    curr_node = random.choice(unseen_neighbors)
                    seen_nodes.add(curr_node)
                    path_length += 1
                longest_path_length = max(path_length, longest_path_length)
        return longest_path_length
    except Exception as e:
        print(f"Exception in graph_longest_path_length: {e}")
        return float('nan')

# instead make a random path!
def graph_largest_connected_component_size(G):
    try:
        components = nx.connected_components(G)
        largest_size = max(len(component) for component in components)
        return largest_size
    except Exception as e:
        print(f"Exception in graph_largest_connected_component_size: {e}")
        return float('nan')

def graph_clique(graph):
    try:
         # Find all maximal cliques
        maximal_cliques = nx.find_cliques(graph)
        
        # Determine the size of the largest clique
        max_clique_size = max(len(clique) for clique in maximal_cliques)
        
        return max_clique_size
    except Exception as e:
        print(f"Exception in graph_clique_number: {e}")
        return float('nan')