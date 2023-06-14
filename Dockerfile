# docker build --tag laptop_docker .
# TEMP: ensure to copy ~/.kube to skypilot root

FROM continuumio/miniconda3:4.11.0

# Install dependencies
RUN conda install -c conda-forge google-cloud-sdk && \
    apt update -y && \
    apt install curl rsync -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

COPY . /sky/

WORKDIR /sky/

# Install sky
RUN cd /sky/ && \
    pip install ".[all]"
