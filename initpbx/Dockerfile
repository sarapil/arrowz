# ===========================================================================
# Arkan Labs - FreePBX 17 + WireGuard VPN (Debian 12 Bookworm)
# ===========================================================================
#
# Base image for FreePBX with full VoIP stack + VPN + monitoring tools
#
# Build:  docker build -t arkan/freepbx:latest .
# Run:    docker compose up -d
#
# Persistent volumes defined in docker-compose.yml ensure all data
# survives container restarts/rebuilds.
# ===========================================================================

FROM debian:bookworm

LABEL maintainer="Arkan Labs <admin@arkan.it.com>"
LABEL description="FreePBX 17 + WireGuard VPN + CoTURN + OpenVPN"
LABEL version="2.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV container=docker
ENV TZ=Asia/Riyadh

# =======================================================================
# 1. Core System + Systemd (Critical for FreePBX services)
# =======================================================================
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        systemd \
        systemd-sysv \
        dbus \
        ca-certificates \
        locales \
        tzdata && \
    # Set timezone
    ln -sf /usr/share/zoneinfo/${TZ} /etc/localtime && \
    echo "${TZ}" > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata && \
    # Generate locale
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    # Remove unnecessary systemd services
    cd /lib/systemd/system/sysinit.target.wants/ && \
    ls | grep -v systemd-tmpfiles-setup | xargs rm -f && \
    # Cleanup
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# =======================================================================
# 2. SSH Server
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server && \
    mkdir -p /var/run/sshd && \
    # Allow root login via SSH
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    # Enable SSH service
    systemctl enable ssh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 3. Development & Build Dependencies (for Asterisk compilation)
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Build essentials
        build-essential \
        autoconf \
        automake \
        libtool \
        pkg-config \
        git \
        wget \
        curl \
        # Asterisk build deps
        uuid-dev \
        libsqlite3-dev \
        libxml2-dev \
        libncurses5-dev \
        libjansson-dev \
        libssl-dev \
        libedit-dev \
        libsrtp2-dev \
        # System libraries
        lsb-release \
        gnupg2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 4. Networking & Diagnostics Tools
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Network utilities
        net-tools \
        iputils-ping \
        iproute2 \
        dnsutils \
        traceroute \
        mtr-tiny \
        nmap \
        # VoIP diagnostics
        sngrep \
        tcpdump \
        tshark \
        # General tools
        vim \
        nano \
        procps \
        htop \
        iftop \
        jq \
        logrotate \
        cron \
        rsync \
        unzip \
        usbutils \
        mariadb-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 5. VPN Stack - WireGuard + OpenVPN
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        # WireGuard
        wireguard-tools \
        qrencode \
        # OpenVPN (legacy support)
        openvpn \
        openvpn-systemd-resolved \
        # IPTables for NAT/forwarding
        iptables \
        iptables-persistent \
        netfilter-persistent && \
    # Enable IP forwarding by default
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.d/99-vpn.conf && \
    echo "net.ipv4.conf.all.proxy_arp=1" >> /etc/sysctl.d/99-vpn.conf && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 6. TURN/STUN Server (for WebRTC)
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        coturn && \
    # Enable coturn service
    echo 'TURNSERVER_ENABLED=1' > /etc/default/coturn && \
    systemctl enable coturn && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 7. Python 3 (for management scripts & Arrowz integration)
# =======================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# =======================================================================
# 8. Persistent Volume Mount Points
# =======================================================================
# Create all directories that will be mounted as persistent volumes
RUN mkdir -p \
    # Asterisk / FreePBX
    /etc/asterisk \
    /var/log/asterisk \
    /var/lib/asterisk \
    /var/spool/asterisk \
    /var/spool/asterisk/monitor \
    /var/spool/asterisk/voicemail \
    /var/spool/asterisk/callaccounting \
    /tftpboot \
    # FreePBX Web UI
    /var/www/html \
    # Database
    /var/lib/mysql \
    # SSL/TLS Certificates
    /etc/ssl/private \
    /etc/letsencrypt \
    # WireGuard VPN
    /etc/wireguard \
    /etc/wireguard/keys \
    /etc/wireguard/peers \
    # OpenVPN
    /etc/openvpn \
    # TURN Server
    /etc/turnserver \
    # SSH keys
    /root/.ssh \
    # Custom scripts
    /opt/arkan/scripts \
    # Backup directory
    /opt/arkan/backups \
    # Shared data
    /opt/arkan/data

# =======================================================================
# 9. Default Configurations
# =======================================================================

# SSH: Prepare authorized_keys directory
RUN chmod 700 /root/.ssh

# WireGuard: Set secure permissions
RUN chmod 700 /etc/wireguard

# IPTables: Create default rules file
RUN mkdir -p /etc/iptables && \
    echo "*filter" > /etc/iptables/rules.v4 && \
    echo ":INPUT ACCEPT [0:0]" >> /etc/iptables/rules.v4 && \
    echo ":FORWARD ACCEPT [0:0]" >> /etc/iptables/rules.v4 && \
    echo ":OUTPUT ACCEPT [0:0]" >> /etc/iptables/rules.v4 && \
    echo "COMMIT" >> /etc/iptables/rules.v4

# =======================================================================
# 10. Health Check
# =======================================================================
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD asterisk -rx "core show channels" 2>/dev/null || exit 1

# =======================================================================
# 11. Expose Ports
# =======================================================================

# SIP
EXPOSE 5060/udp
EXPOSE 5060/tcp
EXPOSE 5061/tcp

# RTP Media (range)
EXPOSE 10000-20000/udp

# Asterisk HTTP/HTTPS/WSS
EXPOSE 8088/tcp
EXPOSE 8089/tcp

# AMI (Asterisk Manager Interface)
EXPOSE 5038/tcp

# FreePBX Web UI
EXPOSE 80/tcp
EXPOSE 443/tcp

# UCP (User Control Panel)
EXPOSE 8001/tcp

# SSH
EXPOSE 22/tcp

# WireGuard VPN
EXPOSE 51820/udp

# OpenVPN
EXPOSE 1194/udp
EXPOSE 1194/tcp

# TURN/STUN
EXPOSE 3478/tcp
EXPOSE 3478/udp
EXPOSE 5349/tcp
EXPOSE 5349/udp
# TURN relay range
EXPOSE 49152-65535/udp

# IAX2 (Inter-Asterisk Exchange)
EXPOSE 4569/udp

# =======================================================================
# 12. Volume Declarations
# =======================================================================
# These volumes MUST be mapped in docker-compose.yml for persistence

# Asterisk / FreePBX Core
VOLUME ["/etc/asterisk"]
VOLUME ["/var/log/asterisk"]
VOLUME ["/var/lib/asterisk"]
VOLUME ["/var/spool/asterisk"]
VOLUME ["/tftpboot"]

# FreePBX Web
VOLUME ["/var/www/html"]

# Database
VOLUME ["/var/lib/mysql"]

# SSL/TLS
VOLUME ["/etc/ssl"]
VOLUME ["/etc/letsencrypt"]

# VPN
VOLUME ["/etc/wireguard"]
VOLUME ["/etc/openvpn"]

# TURN
VOLUME ["/etc/turnserver"]

# SSH & Scripts
VOLUME ["/root/.ssh"]
VOLUME ["/opt/arkan"]

# =======================================================================
# 13. Working Directory & Entrypoint
# =======================================================================
WORKDIR /usr/src

# Systemd as init (required for FreePBX services)
STOPSIGNAL SIGRTMIN+3
CMD ["/lib/systemd/systemd"]
