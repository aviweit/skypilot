# docker build -t 172.31.3.2:5000/sshjumpandserver:latest .

FROM ubuntu:latest

RUN apt update -y && \
    apt install sudo vim openssh-server -y && \
    rm -rf /var/lib/apt/lists/*

# Setup new user [TODO] change to correct user
RUN useradd -m -s /bin/bash weit && \
    echo "weit ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    echo 'Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"' > /etc/sudoers.d/weit

# Switch to weit user
USER weit

# Add /home/weit/.local/bin/ to PATH
RUN echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc

WORKDIR /home/weit
