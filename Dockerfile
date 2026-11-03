# Kali Linux MCP Container
FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    SHELL=/bin/bash \
    KALI_WORKSPACE=/workspace

# Ensure reliable mirror
RUN echo "deb http://kali.download/kali kali-rolling main contrib non-free non-free-firmware" > /etc/apt/sources.list

# Install essential utilities, networking, and security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    bash \
    curl \
    wget \
    git \
    vim \
    nano \
    jq \
    procps \
    tar \
    gzip \
    unzip \
    file \
    ca-certificates \
    net-tools \
    iputils-ping \
    dnsutils \
    whois \
    traceroute \
    tcpdump \
    netcat-traditional \
    socat \
    nmap \
    whatweb \
    nikto \
    gobuster \
    dirb \
    ffuf \
    sqlmap \
    hydra \
    john \
    hashcat \
    exploitdb \
    wordlists \
    metasploit-framework \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Decompress rockyou wordlist if present
RUN if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then gzip -d /usr/share/wordlists/rockyou.txt.gz; fi

# Install Python MCP SDK
RUN pip3 install --no-cache-dir --break-system-packages "mcp[cli]>=1.0.0"

WORKDIR /app
RUN mkdir -p /workspace

COPY server.py /app/server.py
RUN chmod +x /app/server.py

WORKDIR /workspace

CMD ["python3", "/app/server.py"]
