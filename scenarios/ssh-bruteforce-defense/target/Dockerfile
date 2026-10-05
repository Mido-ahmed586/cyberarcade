FROM ubuntu:24.04

RUN apt update && apt install -y openssh-server sudo fail2ban net-tools vim

RUN useradd -m student && echo "student:password123" | chpasswd

RUN mkdir -p /var/run/sshd

RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "PermitRootLogin no" >> /etc/ssh/sshd_config

EXPOSE 22

CMD service ssh start && tail -f /dev/null