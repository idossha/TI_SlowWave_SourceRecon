
# my_plotting.py

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging

###############################################################################
#                      1) PARAMETER VS TIME PLOTTING                          #
###############################################################################

def plot_parameter_time(
    df: pd.DataFrame,
    output_dir: str,
    time_col: str = "Start",
    params_to_plot=None,
    protocol_col: str = "Protocol Number",
    logger: logging.Logger = None
):
    """
    Plots each parameter in params_to_plot vs. time_col, both for each protocol (if protocol_col exists)
    and for all protocols combined. Each scatter is color-coded by 'Classification' (if present).
    Adds a linear trend line for each classification group, plus one overall trend line.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data to plot. Must include `time_col` and `params_to_plot` columns.
    output_dir : str
        Base directory where plots will be saved.
    time_col : str
        Column name in `df` representing time (x-axis).
    params_to_plot : list or None
        List of column names to plot on y-axis. If None, uses a default set.
    protocol_col : str
        Column name representing the protocol. If not found in `df`, we'll skip protocol-based plots.
    logger : logging.Logger
        Logger instance for debug/info messages. If None, no logging is done.
    """

    if params_to_plot is None:
        params_to_plot = ["Frequency", "ValNegPeak", "ValPosPeak", "PTP", "Slope"]

    if logger:
        logger.debug(f"[plot_parameter_time] Plotting these params vs '{time_col}': {params_to_plot}")
    
    # Create subfolders
    per_protocol_dir = os.path.join(output_dir, "plots_per_protocol")
    all_protocols_dir = os.path.join(output_dir, "plots_all_protocols")
    os.makedirs(per_protocol_dir, exist_ok=True)
    os.makedirs(all_protocols_dir, exist_ok=True)

    # Check if the protocol column exists
    if protocol_col in df.columns:
        protocols = df[protocol_col].unique()
    else:
        protocols = []
        if logger:
            logger.warning(f"[plot_parameter_time] Column '{protocol_col}' not found; skipping protocol-based plots.")

    # --- 1. Plot per-protocol ---
    for protocol in protocols:
        subset = df[df[protocol_col] == protocol].copy()
        # Sort by time_col for chronological order
        subset.sort_values(by=time_col, inplace=True)

        for param_col in params_to_plot:
            _plot_one_param_vs_time(
                subset, 
                time_col, 
                param_col, 
                protocol=protocol, 
                output_dir=per_protocol_dir, 
                logger=logger
            )
    
    # --- 2. Plot all protocols combined ---
    df_sorted = df.copy().sort_values(by=time_col)
    for param_col in params_to_plot:
        _plot_one_param_vs_time(
            df_sorted, 
            time_col, 
            param_col, 
            protocol=None,  # combined
            output_dir=all_protocols_dir, 
            logger=logger
        )


def _plot_one_param_vs_time(
    df: pd.DataFrame,
    time_col: str,
    param_col: str,
    protocol=None,
    output_dir="plots",
    logger=None,
    class_col: str = "Classification"
):
    """
    Internal helper function to do the actual time vs. param scatter, 
    color-coded by classification if available. Each classification 
    has its own linear trend line, plus an overall trend line.
    """
    x = df[time_col]
    y = df[param_col]

    # Construct filename and title
    if protocol is not None:
        title_str = f"{param_col} over {time_col} - Protocol {protocol}"
        filename = f"{param_col}_vs_{time_col}_protocol_{protocol}.png"
    else:
        title_str = f"{param_col} over {time_col} - All Protocols Combined"
        filename = f"{param_col}_vs_{time_col}_all_protocols.png"

    # Prepare figure
    plt.figure(figsize=(8, 5))

    # If classification column exists, color-code scatter by classification
    if class_col in df.columns:
        unique_classes = df[class_col].dropna().unique()
        # A simple color palette. Extend for more classes if needed
        colors = ["red", "green", "blue", "purple", "orange", "brown", "pink", "gray"]

        # Plot each classification group
        for idx, cls in enumerate(unique_classes):
            subset = df[df[class_col] == cls]
            x_sub = subset[time_col]
            y_sub = subset[param_col]
            color = colors[idx % len(colors)]
            plt.scatter(x_sub, y_sub, color=color, alpha=0.7, label=f"{cls}")

            # Linear trend line for this classification
            if len(x_sub) > 1:
                coefs = np.polyfit(x_sub, y_sub, 1)
                poly_fn = np.poly1d(coefs)
                plt.plot(x_sub, poly_fn(x_sub), linestyle="--", color=color, alpha=0.9)

        # Overall trend line across all data (regardless of classification)
        if len(x) > 1:
            coefs_all = np.polyfit(x, y, 1)
            poly_fn_all = np.poly1d(coefs_all)
            plt.plot(x, poly_fn_all(x), "k-", linewidth=2, label="Overall Trend")

    else:
        # No classification column; do a single scatter + single line
        plt.scatter(x, y, color="blue", marker="o", label="Data")
        if len(x) > 1:
            coefs = np.polyfit(x, y, 1)
            poly_fn = np.poly1d(coefs)
            plt.plot(x, poly_fn(x), "r--", label="Linear Trend")

    plt.title(title_str)
    plt.xlabel(f"{time_col} (s)")
    plt.ylabel(param_col)
    plt.legend()
    plt.tight_layout()
    
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path)
    plt.close()

    if logger:
        logger.debug(f"[_plot_one_param_vs_time] param_col={param_col}, protocol={protocol}, saved -> {save_path}")


###############################################################################
#                         2) PTP VS. SLOPE PLOTTING                           #
###############################################################################

def plot_ptp_slope_by_classification(
    df: pd.DataFrame,
    output_dir: str,
    ptp_col: str = "PTP",
    slope_col: str = "Slope",
    class_col: str = "Classification",
    protocol_col: str = "Protocol Number",
    logger: logging.Logger = None
):
    """
    Plots PTP vs. Slope with color-coded Classification groups, including
    one linear trend line per classification group.

    Also does protocol-based subsets if `protocol_col` is found.
    """
    if logger:
        logger.debug("[plot_ptp_slope_by_classification] Called.")
    
    # Create subfolders
    per_protocol_dir = os.path.join(output_dir, "plots_per_protocol")
    all_protocols_dir = os.path.join(output_dir, "plots_all_protocols")
    os.makedirs(per_protocol_dir, exist_ok=True)
    os.makedirs(all_protocols_dir, exist_ok=True)

    # Protocol-based if the column exists
    if protocol_col in df.columns:
        protocols = df[protocol_col].unique()
    else:
        protocols = []
        if logger:
            logger.warning(f"[plot_ptp_slope_by_classification] '{protocol_col}' not found.")

    # 1. Plot per-protocol
    for protocol in protocols:
        subset = df[df[protocol_col] == protocol]
        _plot_ptp_slope_by_class(
            subset,
            ptp_col,
            slope_col,
            class_col,
            protocol=protocol,
            output_dir=per_protocol_dir,
            logger=logger
        )

    # 2. Plot combined (all protocols)
    _plot_ptp_slope_by_class(
        df,
        ptp_col,
        slope_col,
        class_col,
        protocol=None,
        output_dir=all_protocols_dir,
        logger=logger
    )


def _plot_ptp_slope_by_class(
    df: pd.DataFrame,
    ptp_col: str,
    slope_col: str,
    class_col: str,
    protocol=None,
    output_dir="plots",
    logger=None
):
    """
    Internal helper to plot PTP vs slope color-coded by classification.
    """
    if logger:
        logger.debug(f"[_plot_ptp_slope_by_class] protocol={protocol}")
    if class_col not in df.columns:
        if logger:
            logger.warning(f"[_plot_ptp_slope_by_class] '{class_col}' column missing. Skipping plot.")
        return

    unique_classes = df[class_col].dropna().unique()
    # A simple color palette. Extend if you have more classes
    colors = ["red", "green", "blue", "purple", "orange"]

    if protocol is not None:
        title_str = f"{ptp_col} vs. {slope_col} - Protocol {protocol}"
        filename = f"{ptp_col}_vs_{slope_col}_protocol_{protocol}.png"
    else:
        title_str = f"{ptp_col} vs. {slope_col} - All Protocols Combined"
        filename = f"{ptp_col}_vs_{slope_col}_all_protocols.png"

    plt.figure(figsize=(8, 5))
    for idx, cls in enumerate(unique_classes):
        class_subset = df[df[class_col] == cls]
        x = class_subset[ptp_col]
        y = class_subset[slope_col]

        color = colors[idx % len(colors)]
        plt.scatter(x, y, color=color, alpha=0.7, label=str(cls))

        if len(x) > 1:
            coefs = np.polyfit(x, y, 1)
            poly_fn = np.poly1d(coefs)
            plt.plot(x, poly_fn(x), linestyle="--", color=color)

    plt.title(title_str)
    plt.xlabel(ptp_col)
    plt.ylabel(slope_col)
    plt.legend(title=class_col)
    plt.tight_layout()

    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path)
    plt.close()

    if logger:
        logger.debug(f"[_plot_ptp_slope_by_class] Saved -> {save_path}")


###############################################################################
#                          3) PTP HISTOGRAM PLOTTING                          #
###############################################################################

def plot_ptp_histogram(
    df: pd.DataFrame,
    output_dir: str,
    ptp_col: str = "PTP",
    protocol_col: str = "Protocol Number",
    logger: logging.Logger = None
):
    """
    Plots a histogram of PTP for each protocol, plus an all-protocols-combined plot.
    """
    if logger:
        logger.debug("[plot_ptp_histogram] Called.")

    per_protocol_dir = os.path.join(output_dir, "plots_per_protocol")
    all_protocols_dir = os.path.join(output_dir, "plots_all_protocols")
    os.makedirs(per_protocol_dir, exist_ok=True)
    os.makedirs(all_protocols_dir, exist_ok=True)

    if protocol_col in df.columns:
        protocols = df[protocol_col].unique()
    else:
        protocols = []
        if logger:
            logger.warning(f"[plot_ptp_histogram] '{protocol_col}' not found.")

    # 1. Protocol-based
    for protocol in protocols:
        subset = df[df[protocol_col] == protocol]
        _plot_ptp_hist_one(subset, ptp_col, protocol=protocol, output_dir=per_protocol_dir, logger=logger)

    # 2. All combined
    _plot_ptp_hist_one(df, ptp_col, protocol=None, output_dir=all_protocols_dir, logger=logger)


def _plot_ptp_hist_one(
    df: pd.DataFrame,
    ptp_col: str,
    protocol=None,
    output_dir="plots",
    logger=None
):
    """
    Internal helper function to plot a single histogram of PTP.
    """
    x = df[ptp_col]

    if protocol is not None:
        title_str = f"{ptp_col} Histogram - Protocol {protocol}"
        filename = f"{ptp_col}_histogram_protocol_{protocol}.png"
    else:
        title_str = f"{ptp_col} Histogram - All Protocols Combined"
        filename = f"{ptp_col}_histogram_all_protocols.png"

    plt.figure(figsize=(8, 5))
    plt.hist(x, bins="auto", color="cyan", alpha=0.7, edgecolor="black")
    plt.xlabel(ptp_col)
    plt.ylabel("Number of Waves")
    plt.title(title_str)
    plt.tight_layout()

    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path)
    plt.close()

    if logger:
        logger.debug(f"[_plot_ptp_hist_one] Saved histogram -> {save_path}")

