
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd


def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)#, with_labels=True)
    plt.title("Directed Graph Visualization")
    plt.show()


def plot_data(csv_path):
    lines_count = 5
    bins_count = 32
    quant_fill = 0.05

    df = pd.read_csv(csv_path)

    # Ensure the data has X, Y, and other columns
    if "conflict_percentage" not in df.columns or "txs" not in df.columns:
        raise ValueError("The CSV file must contain 'X' and 'Y' columns.")

    # Extract X, Y, and property columns
    properties = df.drop(columns=["conflict_percentage", "txs"]).columns
    
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
            conflict_percentage = df_group["conflict_percentage"]
            
            # Bin the 'prop' data
            bins = np.linspace(conflict_percentage.min(), conflict_percentage.max(), num=bins_count)  # Adjust 'num' for bin granularity
            df_group['conflict_percentage_bin'] = pd.cut(conflict_percentage, bins=bins, include_lowest=True)
            
            # Group by the bins and compute mean and SEM
            grouped = df_group.groupby('conflict_percentage_bin')
            mean_conflict = grouped["conflict_percentage"].mean()
            mean_prop = grouped[prop].mean()
            
            low_prop = grouped[prop].quantile(quant_fill)
            hi_prop = grouped[prop].quantile(1-quant_fill)

            # Plot mean conflict_percentage with confidence intervals
            plt.plot(mean_conflict, mean_prop, label=f"#txs>{int(txs_min)}")
            plt.fill_between(mean_conflict,
                            low_prop,
                            hi_prop,
                            alpha=0.2)  # Adjust 'alpha' for transparency
            
        plt.grid()
        plt.title(f"{prop}")
        plt.ylabel(f"{prop}")
        plt.xlabel("conflict_percentage")
        plt.tight_layout()
        plt.legend()

        # Save the plot
        plt.savefig(f"scatter_{prop}.png")
        plt.close()

    print("Plots have been generated and saved as PNG files.")