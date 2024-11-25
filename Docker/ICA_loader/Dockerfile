
# Base image
FROM mathworks/matlab:r2024b

# Install necessary tools
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    build-essential

# Set working directory to /home
WORKDIR /home

# Download and install EEGLAB
RUN wget https://sccn.ucsd.edu/eeglab/download/daily/eeglab2024.2.zip -O eeglab2024.2.zip && \
    unzip eeglab2024.2.zip && \
    mv eeglab2024.2 eeglab

# Download and install AMICA plugin
RUN wget https://sccn.ucsd.edu/eeglab/plugins/AMICA1.5.2.zip -O AMICA1.5.2.zip && \
    unzip AMICA1.5.2.zip -d eeglab/plugins/ && \
    mv eeglab/plugins/AMICA1.5.2 eeglab/plugins/AMICA

# Clone your GitHub repository
RUN git clone https://github.com/idossha/EEG_ICA.git

# Create MATLAB script to set up EEGLAB
RUN echo "addpath('/home/eeglab'); savepath; eeglab('nogui'); exit;" > setup_eeglab.m

# Run MATLAB script to set up EEGLAB and AMICA plugin
RUN matlab -batch "run('/home/setup_eeglab.m');"

# Set the working directory to the cloned GitHub repository
WORKDIR /home/EEG_ICA

# Set the entrypoint to bash for interactive terminal
ENTRYPOINT ["/bin/bash"]

