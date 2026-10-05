FROM cyberarcade/kali-lab:latest

# Install tmux (keeps Guacamole terminal alive) and libcap2-bin (grants nmap raw-socket access)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends tmux libcap2-bin && \
    rm -rf /var/lib/apt/lists/*

# Student user with the credentials Guacamole expects
# ssl-cert group + 750 on /etc/ssl/private allows Metasploit's bootsnap to scan the path
RUN useradd -m -s /bin/bash student && \
    echo "student:cyber123" | chpasswd && \
    usermod -aG sudo,ssl-cert student && \
    echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chmod 750 /etc/ssl/private && \
    setcap cap_net_raw,cap_net_admin+ep /usr/lib/nmap/nmap

# Enable SSH password auth
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes"        >> /etc/ssh/sshd_config && \
    mkdir -p /var/run/sshd

# Auto-attach to the tmux 'lab' session on login (matches guac_autosolve TMUX_SESSION)
# The loop restarts tmux if the student accidentally exits the session
RUN printf '[ -z "$TMUX" ] && while true; do tmux new-session -A -s lab && break; done\n' \
    >> /home/student/.bashrc

EXPOSE 22
