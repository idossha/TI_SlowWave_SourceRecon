#!/usr/bin/env bash

# A Bash script to compile PDFs with different layout options.

# ---- USER CONFIGURATIONS ----
PROJECT_DIR="/Volumes/CSC-Ido/Analyze/"
SUBJECTS=("101" "102" "107" "108" "109" "110" "111" "112" "114" "115" "116" "117" "119" "120" "121" "122" "127" "132")
# SUBJECTS=("101")
NIGHTS=("N1")
# IMAGES=(
#   "spectrogram.png"
#   "stim_durations.png"
#   "net_coverage_2D.png"
#   "first_vs_last/Frequency_first_vs_last_hour.png"
#   "first_vs_last/PTP_first_vs_last_hour.png"
#   "first_vs_last/Slope_first_vs_last_hour.png"
#   "first_vs_last/Left_Frontal/Frequency_first_vs_last_Left_Frontal.png"
#   "first_vs_last/Left_Frontal/PTP_first_vs_last_Left_Frontal.png"
#   "first_vs_last/Left_Frontal/Slope_first_vs_last_Left_Frontal.png"
#   "first_vs_last/Right_Frontal/Frequency_first_vs_last_Right_Frontal.png"
#   "first_vs_last/Right_Frontal/PTP_first_vs_last_Right_Frontal.png"
#   "first_vs_last/Right_Frontal/Slope_first_vs_last_Right_Frontal.png"
#   "first_vs_last/Parietal/Frequency_first_vs_last_Parietal.png"
#   "first_vs_last/Parietal/PTP_first_vs_last_Parietal.png"
#   "first_vs_last/Parietal/Slope_first_vs_last_Parietal.png"
#   "overall_counts_filtered.png"
#   "overall_mean_values_filtered.png"
#   "region_posterior_counts_filtered.png"
#   "region_posterior_mean_values_filtered.png"
#   "region_R_frontal_counts_filtered.png"
#   "region_R_frontal_mean_values_filtered.png"
#   "region_L_frontal_counts_filtered.png"
#   "region_L_frontal_mean_values_filtered.png"
#   "plots_all_protocols/Frequency_vs_Start_all_protocols.png"
#   "plots_all_protocols/Slope_vs_Start_all_protocols.png"
#   "plots_all_protocols/PTP_vs_Start_all_protocols.png"
#   "plots_all_protocols/PTP_vs_Slope_all_protocols.png"
# )
#
#
#
IMAGES=(

  "first_z_wave_counts_topoplot_${SUBJECTS[@]}_N1"
  "biggest_z_wave_counts_topoplot_${SUBJECTS[@]}_N1"
  "all_z_wave_counts_topoplot_${SUBJECTS[@]}_N1"



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
  layout3)
    # Example: 2x2, 3x2, 1x2x2
    python3 visualizer.py "$PROJECT_DIR" \
      --subjects "${SUBJECTS[@]}" \
      --nights "${NIGHTS[@]}" \
      --images "${IMAGES[@]}" \
      --layouts single 1x2 3x1 3x3 2x2 2x2 2x2 \
      --margin "$MARGIN"
    ;;
  *)
    # Unknown argument
    echo "Error: Unknown option '$1'"
    usage
    ;;
esac

