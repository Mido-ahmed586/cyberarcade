#!/bin/bash

docker exec cyber_target bash -c "

echo '[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 600
findtime = 600
' > /etc/fail2ban/jail.local

service fail2ban restart

echo '=== FAIL2BAN STATUS ==='

fail2ban-client status sshd
"