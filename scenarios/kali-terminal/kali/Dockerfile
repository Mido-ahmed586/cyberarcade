FROM kalilinux/kali-rolling

# ── Reliable mirror ───────────────────────────────────────────────────────────
RUN printf "deb http://kali.download/kali kali-rolling main contrib non-free non-free-firmware\n" \
    > /etc/apt/sources.list

# ── System + SSH + forensics tools ───────────────────────────────────────────
RUN apt-get clean && apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        # SSH + shell + cron (cron provides crontab binary, needed for Lab 7)
        openssh-server sudo tmux nano vim curl wget \
        cron iputils-ping net-tools procps \
        # Core tools used directly in lab tasks
        binutils file zip unzip tree less bsdmainutils \
        # Forensics tools used directly in lab tasks
        sleuthkit \
        steghide \
        binwalk \
        foremost \
        libimage-exiftool-perl \
        testdisk \
        dc3dd \
        ewf-tools \
        # Image creation (to generate JPEG evidence files for steghide)
        imagemagick \
        # ext2 image creation without root (for disk image lab)
        genext2fs \
        e2fsprogs \
        # Python + pip
        git python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Volatility 3 (best-effort — lab tasks use strings/grep, not vol CLI)
RUN python3 -m venv /opt/venv3 && \
    /opt/venv3/bin/python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv3/bin/pip install --no-cache-dir volatility3 && \
    ln -sf /opt/venv3/bin/vol /usr/local/bin/vol && \
    ln -sf /opt/venv3/bin/volshell /usr/local/bin/volshell && \
    printf '#!/bin/sh\nexec /opt/venv3/bin/vol "$@"\n' > /usr/local/bin/volatility3 && \
    chmod +x /usr/local/bin/volatility3 || echo "[warn] volatility3 install failed — lab still functional"

# ── Student user ──────────────────────────────────────────────────────────────
RUN useradd -m -s /bin/bash student && \
    echo "student:student123" | chpasswd && \
    usermod -aG sudo student && \
    echo "student ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# ── SSH config ────────────────────────────────────────────────────────────────
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes"        >> /etc/ssh/sshd_config && \
    mkdir -p /var/run/sshd && \
    mv /etc/profile.d/80-systemd-osc-context.sh \
       /etc/profile.d/80-systemd-osc-context.sh.disabled 2>/dev/null || true

# ── Build evidence files ──────────────────────────────────────────────────────
COPY setup_evidence.sh /tmp/setup_evidence.sh
RUN chmod +x /tmp/setup_evidence.sh && /tmp/setup_evidence.sh && rm /tmp/setup_evidence.sh

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
