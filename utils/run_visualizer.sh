#!/usr/bin/env bash

# A Bash script to compile PDFs with different layout options.

# ---- USER CONFIGURATIONS ----
PROJECT_DIR="/Volumes/CSC-Ido/DATA_not_to_be_worked_w_directly"
# SUBJECTS=("101" "102")
SUBJECTS=("101" "102" "107" "110" "115" "116" "119" "121" "123" "127" "128")
NIGHTS=("N1")
IMAGES=(
  "spectrogram.png"
  "stim_durations.png"
  "net_coverage_2D.png"
  "overall_counts_filtered.png"
  "overall_mean_values_filtered.png"
  "region_posterior_counts_filtered.png"
  "region_posterior_mean_values_filtered.png"
  "region_R_frontal_counts_filtered.png"
  "region_R_frontal_mean_values_filtered.png"
  "region_L_frontal_counts_filtered.png"
  "region_L_frontal_mean_values_filtered.png"
)

MARGIN=0.25

# Usage message
usage() {
  echo "Usage: $0 <option>"
  echo
  echo "Available options:"
  echo "  layout1    → single 1x2 2x2 2x2"
  echo "  layout2    → 2x2 3x2 1x2x2"
  echo
  echo "Feel free to add or modify layout sets below."
  exit 1
}

# If no argument was provided, print usage
if [ $# -lt 1 ]; then
    usage
fi

# Run visualizer.py with different layouts based on the first argument
case "$1" in
  layout1)
    # Example: single, 1x2, 2x2, 2x2
    python3 visualizer.py "$PROJECT_DIR" \
      --subjects "${SUBJECTS[@]}" \
      --nights "${NIGHTS[@]}" \
      --images "${IMAGES[@]}" \
      --layouts single 1x2 2x2 2x2 \
      --margin "$MARGIN"
    ;;
  layout2)
    # Example: 2x2, 3x2, 1x2x2
    python3 visualizer.py "$PROJECT_DIR" \
      --subjects "${SUBJECTS[@]}" \
      --nights "${NIGHTS[@]}" \
      --images "${IMAGES[@]}" \
      --layouts 2x2 3x2 1x2x2 \
      --margin "$MARGIN"
    ;;
  *)
    # Unknown argument
    echo "Error: Unknown option '$1'"
    usage
    ;;
esac

