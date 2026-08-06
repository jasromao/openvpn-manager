#!/bin/bash

set -e

echo "======================================="
echo "  Instalar OpenVPN Manager"
echo "======================================="

apt update
apt install -y python3 python3-pip python3-flask python3-flask-httpauth python3-venv git

mkdir -p /opt

if [ -d /opt/openvpn-manager ]; then
    rm -rf /opt/openvpn-manager
fi

git clone https://github.com/Jasromao/openvpn-manager.git /opt/openvpn-manager

cd /opt/openvpn-manager

echo "A descarregar backup..."

wget -O /tmp/openvpn-manager.tar.gz \
https://github.com/jasromao/openvpn-manager/releases/download/v1.0/openvpn-manager-2026-08-06_08-27-50.tar.gz

cd /opt
tar -xzf /tmp/openvpn-manager.tar.gz

cat >/etc/systemd/system/openvpn-manager.service <<EOF
[Unit]
Description=OpenVPN Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/openvpn-manager
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF


echo "A criar remote-host.conf..."

PUBLIC_IP=$(curl -4 -s ifconfig.me)

if [ -n "$PUBLIC_IP" ]; then
    echo "$PUBLIC_IP" | sudo tee /etc/openvpn/remote-host.conf >/dev/null
    sudo chmod 644 /etc/openvpn/remote-host.conf
fi

cp /opt/openvpn-manager/criar-cliente-ovpn-web /usr/local/bin/
chmod +x /usr/local/bin/criar-cliente-ovpn-web

systemctl daemon-reload
systemctl enable openvpn-manager
systemctl restart openvpn-manager

echo
echo "======================================="
echo "Instalação concluída!"
echo "Painel: http://IP_DA_VPS:5000"
echo "======================================="
