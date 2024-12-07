
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx

def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)#, with_labels=True)
    plt.title("Directed Graph Visualization")
    plt.show()


def plot_data(csv_path):
    markers = ["o", "s", "^", "v", "D", "*"]
    
    lines_count = 4
    bins_count = 16
    quant_fill = 0.05

    df = pd.read_csv(csv_path)

    # Ensure the data has X, Y, and other columns
    if "density" not in df.columns or "txs" not in df.columns:
        raise ValueError("The CSV file must contain 'X' and 'Y' columns.")

    # Extract X, Y, and property columns
    properties = df.drop(columns=["density"]).columns
    
    split_values = df["txs"].quantile([i / (lines_count + 1) for i in range(1, lines_count + 1)])
    split_values = sorted(list(split_values))
    # Create heatmaps for each property
    for prop in properties:
        plt.figure(figsize=(8, 6))
        for i_tx_group in range(len(split_values) + 1):
            if i_tx_group == 0:
                txs_min = 0
                txs_max = split_values[i_tx_group]
            elif i_tx_group == len(split_values):
                txs_min = split_values[i_tx_group - 1]
                txs_max = float('inf')
            else:
                txs_min = split_values[i_tx_group - 1]
                txs_max = split_values[i_tx_group]

            # Select the data for the current tx_group
            df_group = df.loc[(df["txs"] < txs_max) & (df["txs"] > txs_min)].sort_values(by=prop)
            
            # Copy to avoid SettingWithCopyWarning
            df_group = df_group.copy()
            
            prop_data = df_group[prop]
            density = df_group["density"]
            
            # Bin the 'prop' data
            bins = np.linspace(density.min(), density.max(), num=bins_count)  # Adjust 'num' for bin granularity
            df_group['density_bin'] = pd.cut(density, bins=bins, include_lowest=True)
            
            # Group by the bins and compute mean and SEM
            grouped = df_group.groupby('density_bin')
            mean_conflict = grouped["density"].mean()
            mean_prop = grouped[prop].mean()
            
            low_prop = grouped[prop].quantile(quant_fill)
            hi_prop = grouped[prop].quantile(1-quant_fill)

            # Plot mean density with confidence intervals
            plt.plot(mean_conflict, mean_prop, label=f"#txs>{int(txs_min)}", marker=markers[i_tx_group])
            plt.fill_between(mean_conflict,
                            low_prop,
                            hi_prop,
                            alpha=0.2)  # Adjust 'alpha' for transparency
            
        plt.grid()
        plt.title(f"{prop}")
        plt.ylabel(f"{prop}")
        plt.xlabel("density")
        plt.tight_layout()
        plt.legend()

        # Save the plot
        plt.savefig(f"figures\\{prop}.png")
        plt.close()

    print("Plots have been generated and saved as PNG files.")