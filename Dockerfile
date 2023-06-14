###
# cd ~
# docker build --tag laptop_docker -f skypilot/Dockerfile .

FROM continuumio/miniconda3:4.11.0

# Install dependencies
RUN conda install -c conda-forge google-cloud-sdk && \
    apt update -y && \
    apt install vim curl rsync -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

COPY skypilot/ /sky/

WORKDIR /sky/

# Install sky
RUN cd /sky/ && \
    pip install ".[all]" && \
    pip install kubernetes

COPY ./.kube /root/.kube

RUN echo "set mouse-=a" >> /root/.vimrc

RUN mkdir -p  /root/.sky/catalogs/v5/kubernetes/


RUN echo "InstanceType,AcceleratorName,AcceleratorCount,vCPUs,MemoryGiB,GpuInfo,Price,SpotPrice,Region,AvailabilityZone" >> /root/.sky/catalogs/v5/kubernetes/vms.csv && \
    echo "cpu1,,,1,1,,0,0,kubernetes,kubernetes" >> /root/.sky/catalogs/v5/kubernetes/vms.csv
