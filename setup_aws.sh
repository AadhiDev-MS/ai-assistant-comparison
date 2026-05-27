#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

echo "Updating packages..."
sudo apt-get update -y

echo "Installing NVIDIA drivers (this takes a few minutes)..."
sudo apt-get install -y nvidia-driver-535

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "Configuring Ollama to listen on 0.0.0.0..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
echo '[Service]' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
echo 'Environment="OLLAMA_HOST=0.0.0.0"' | sudo tee -a /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo "Pulling Llama 3.2 model (this may take a few minutes depending on AWS network)..."
# We use 'pull' instead of 'run' so it downloads in the background and exits cleanly
ollama pull llama3.2

echo "Setup complete! Rebooting server to apply GPU drivers..."
sudo reboot
