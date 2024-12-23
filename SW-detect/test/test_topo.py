# test_plot_topomaps.py

import os
import logging
from plot_topomaps import plot_topomaps

def setup_logging():
    """
    Set up basic logging to console.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Set up logging
    setup_logging()

    # Hardcoded paths
    # Replace these paths with your actual file paths
    set_file = "/Users/idohaber/Desktop/output/annotated_raw_filtered.set"
    output_dir = "/Users/idohaber/Desktop/output"
    suffix = "filtered"

    # Check if the set_file exists
    if not os.path.exists(set_file):
        logging.error(f"The annotated .set file does not exist at: {set_file}")
        return

    # Call the plot_topomaps function
    plot_topomaps(set_file, output_dir, suffix)

if __name__ == "__main__":
    main()
