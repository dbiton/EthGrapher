
# EthGrapher

EthGrapher is a Python project designed for analyzing and visualizing Ethereum blockchain data. 
It provides tools to fetch, parse, and graph Ethereum data, calculate metrics, and produce insightful visualizations.

## Project Structure

- **main.py**: The main entry point of the application. Run this file to execute the project.
- **fetchers.py**: Contains functions for fetching Ethereum data from relevant sources.
- **parsers.py**: Provides utilities for parsing the fetched data into usable formats.
- **loaders.py**: Handles loading pre-existing data or resources into the program.
- **savers.py**: Contains functions to save processed data or outputs.
- **graph_metrics.py**: Includes methods for computing various graph metrics on Ethereum network data.
- **plotters.py**: Responsible for visualizing data and generating plots or graphs.
- **ethereum_ledger.pkl**: A preloaded dataset of the Ethereum ledger in serialized form.
- **requirements.txt**: Lists all the Python dependencies required to run the project.

## Features

1. **Data Fetching**: Retrieve Ethereum blockchain data efficiently.
2. **Data Parsing**: Convert raw data into structured formats for further processing.
3. **Graph Analysis**: Calculate metrics and insights from Ethereum transaction graphs.
4. **Visualization**: Create graphs and visualizations to better understand the data.

## Installation

1. Clone the repository or extract the project files.
2. Navigate to the project directory.
3. Install the required dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Prepare the necessary data (e.g., Ethereum ledger data) or use the provided `ethereum_ledger.pkl`.
2. Run the main script to start the analysis and visualization process:
   ```bash
   python main.py
   ```

## Dependencies

The project requires the following Python packages (specified in `requirements.txt`):

## Contact

For any questions or issues, please contact the project maintainer.

