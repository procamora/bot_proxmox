# bot_proxmox
This is a bot to turn on and off a computer with Proxmox using wake on lan and ssh




 sudo apt install wakeonlan
 pip3 install - r requirements.txt --user
 pip3 install - r Pentesting/requirements.txt --user
 
 

```
[BASICS]
BOT_TOKEN = TOKEN
MAC_PROXMOX = AA:AA:AA:AA:AA:AA

[SSH]
IP = 192.168.1.20
USER = root
PASSWORD = password
PORT = 22
CERT = /tmp/id_rsa
```