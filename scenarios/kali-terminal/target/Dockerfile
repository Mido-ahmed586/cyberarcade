FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openssh-server \
    sudo \
    curl \
    net-tools \
    iputils-ping \
    nano \
    python3 \
    && mkdir -p /var/run/sshd

RUN useradd -m -s /bin/bash defender && \
    echo "defender:defender123" | chpasswd && \
    usermod -aG sudo defender && \
    echo "defender ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN useradd -m -s /bin/bash victim && \
    echo "victim:password123" | chpasswd

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]