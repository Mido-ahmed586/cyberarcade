FROM kalilinux/kali-rolling

RUN printf "deb http://kali.download/kali kali-rolling main contrib non-free non-free-firmware\n" > /etc/apt/sources.list

RUN apt clean && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install -y --no-install-recommends \
    nmap \
    hydra \
    openssh-client \
    iputils-ping \
    netcat-traditional \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]