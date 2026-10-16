#!/usr/bin/env bash
# Runs ONCE, as root, the first time the EC2 server boots (passed as "user data").
set -euxo pipefail

# Docker + the Compose plugin from Ubuntu's own packages.
# Lock timeout: on first boot Ubuntu's own auto-updates may hold the apt lock.
APT="apt-get -o DPkg::Lock::Timeout=600"
$APT update
$APT install -y docker.io docker-compose-v2 rsync
systemctl enable --now docker
usermod -aG docker ubuntu # let the ubuntu user run docker without sudo

# 2 GB swap: headroom if building the image and Postgres need memory at the same time
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Install security updates automatically
$APT install -y unattended-upgrades

touch /var/lib/waitwatch-ready # deploy waits for this file
