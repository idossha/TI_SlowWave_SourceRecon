
# Use Buildx to specify the platform if building on an ARM64 machine
# Build command:
# docker buildx build --platform linux/amd64 -t idossha/ica-csc:v0.0.5 --load .

# Base image
FROM mathworks/matlab:r2024b

# Switch to root user to install packages
USER root

# Install necessary tools and execstack
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    vim \
    tar \
    bzip2 \
    gcc \
    g++ \
    cmake \
    autoconf \
    automake \
    build-essential \
    pkg-config \
    libtool \
    libncurses5-dev \
    libgtk2.0-dev \
    libxt-dev \
    libx11-dev \
    execstack 

# Set working directory to /home/matlab
WORKDIR /home

# Download and install EEGLAB
RUN wget https://sccn.ucsd.edu/eeglab/download/daily/eeglab2024.2.zip -O eeglab2024.2.zip && \
    unzip eeglab2024.2.zip && \
    rm eeglab2024.2.zip

# Download and install AMICA plugin
RUN wget https://sccn.ucsd.edu/eeglab/plugins/AMICA1.5.2.zip -O AMICA1.5.2.zip && \
    unzip AMICA1.5.2.zip -d eeglab2024.2/plugins/AMICA1.5.2/ && \
    rm AMICA1.5.2.zip

# Clone your GitHub repository
RUN git clone https://github.com/idossha/EEG_ICA.git

# Set the working directory to the cloned GitHub repository
WORKDIR /home/matlab/EEG_ICA

# Clear executable stack flag on MATLAB's shared libraries
RUN execstack -c /opt/matlab/R2024b/bin/glnxa64/libmwblas.so && \
    execstack -c /opt/matlab/R2024b/bin/glnxa64/libmwfoundation_crash_handling.so

# Set the working directory to the cloned GitHub repository
WORKDIR /home/matlab/EEG_ICA

# Set the entrypoint to bash for interactive terminal
ENTRYPOINT ["/bin/bash"]

