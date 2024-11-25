
# Use Buildx to specify the platform if building on an ARM64 machine
# Build command:
# docker buildx build --platform linux/amd64 -t matlab_eeglab_amica:latest --load .

# Base image
FROM mathworks/matlab:r2024b

# Switch to root user to install packages
USER root

# Install necessary tools
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    build-essential

# Set working directory to /home/matlab
WORKDIR /home

# Ensure ownership of /home/matlab
RUN chown -R matlab:matlab /home/matlab

# Download and install EEGLAB
RUN wget https://sccn.ucsd.edu/eeglab/download/daily/eeglab2024.2.zip -O eeglab2024.2.zip && \
    unzip eeglab2024.2.zip 

# Download and install AMICA plugin
RUN wget https://sccn.ucsd.edu/eeglab/plugins/AMICA1.5.2.zip -O AMICA1.5.2.zip && \
    unzip AMICA1.5.2.zip -d eeglab2024.2/plugins/AMICA1.5.2/

# Clone your GitHub repository
RUN git clone https://github.com/idossha/EEG_ICA.git

# Set the working directory to the cloned GitHub repository
WORKDIR /home/EEG_ICA

ENTRYPOINT ["/bin/bash"]
