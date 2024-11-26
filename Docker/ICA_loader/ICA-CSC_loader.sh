
#!/bin/bash

###############################################
# run_ica_loader.sh - Script to run ICA analysis on .set files in a given directory
#
# Dependencies:
# 1. Docker installed and running
# 2. Your Docker image: idossha/ica-csc:v0.1.0
# 3. Mounted directory with your project data
###############################################

# Set script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Function to check allocated Docker resources (CPU, memory)
check_docker_resources() {
  echo "Checking Docker resource allocation..."

  if docker info >/dev/null 2>&1; then
    # Get Docker's memory and CPU allocation
    MEMORY=$(docker info --format '{{.MemTotal}}')
    CPU=$(docker info --format '{{.NCPU}}')

    # Convert memory from bytes to GB
    MEMORY_GB=$(echo "scale=2; $MEMORY / (1024^3)" | bc)
    echo "Docker Memory Allocation: ${MEMORY_GB} GB"
    echo "Docker CPU Allocation: $CPU CPUs"
  else
    echo "Docker is not running or not installed. Please start Docker and try again."
    exit 1
  fi
}

# Function to validate and prompt for the project directory
get_project_directory() {
  while true; do
    echo "Give path to local project dir:"
    read -r LOCAL_PROJECT_DIR

    if [[ -d "$LOCAL_PROJECT_DIR" ]]; then
      echo "Project directory found."
      break
    else
      echo "Invalid directory. Please provide a valid path."
    fi
  done
}


# Function to display welcome message
display_welcome() {
  echo " "
  echo "#####################################################################"
  echo "Parallel ICA on remote server from the Center for Sleep and Consciousness"
  echo "Developed by Ido Haber"
  echo " "
  echo "#####################################################################"
  echo " "
}

# Function to run Docker and execute the ICA script
run_docker() {
  echo "Starting Docker container to run ICA analysis..."

  docker run -ti --rm \
    --security-opt seccomp=unconfined \
    -v "$LOCAL_PROJECT_DIR":/mnt/ \
    -w /home/matlab/EEG_ICA/parallel-ICA \
    idossha/ica-csc:v0.1.0 \
    #bash run_ica.sh /mnt/test

  if [[ $? -ne 0 ]]; then
    echo "Error: Docker container exited with an error."
    exit 1
  fi
}

# Main Script Execution

display_welcome
check_docker_resources
get_project_directory
validate_run_ica_script

run_docker

echo "ICA analysis completed successfully."

