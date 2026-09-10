#!/bin/bash

# Run command
# sudo -E ./setup.sh

set -e

source /etc/environment

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  echo "eg: sudo -E ${0}"
  exit
fi

WORKDIR=$(pwd)

RED='\033[0;31m'
L_GREEN='\033[1;32m'
D_GREEN='\033[0;32m'
L_BLUE='\033[1;34m'
D_BLUE='\033[0;34m'
L_RED='\033[1;31m'
D_RED='\033[0;31m'
L_YEL='\033[1;33m'
D_YEL='\033[0;33m'
NC='\033[0m'

setupPythonDep() {
  echo -e "${L_GREEN}Check Python dependencies${NC}"
  apt install -y build-essential python3-dev python3-pip
  python3 -m pip install -q --upgrade --no-cache-dir pip > /dev/null
  python3 -m pip install -q --no-cache-dir -r requirements.txt > /dev/null
  echo -e "${D_GREEN}Python dependencies OK${NC}"
}

setupToolDep() {
  echo -e "${L_GREEN}Check tool dependencies${NC}"
  apt install -y i2c-tools
  echo -e "${D_GREEN}Tool dependencies OK${NC}"
}

# generic function that check docker & docker-compose installed
setupDocker() {
  echo -e "${L_GREEN}Check Docker Engine dependencies${NC}"
  if ! [ -x "$(command -v docker)" ]; then
    install_docker
  else
    DOCKER_VERSION=$(docker version -f "{{.Server.Version}}")
    if ! [[ $DOCKER_VERSION == *"20.10."* ]]; then
      install_docker
    fi
    echo -e "${D_GREEN}Docker & docker-compose OK${NC}"
  fi
}

install_docker() {
  echo -e "Downloading & installing 'docker & docker-compose'"
  $PROXY apt update &&
  $PROXY apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common &&
        mkdir -p /etc/apt/keyrings &&
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg &&
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null &&
        apt update &&
        apt install -y docker docker-ce docker-ce-cli containerd.io docker-compose-plugin &&
        usermod -aG docker $USER
}


main() {
  setupPythonDep
  setupToolDep
  setupDocker
  echo -e "${L_YEL}Please Restart Before Proceed ${NC}"
}

main
