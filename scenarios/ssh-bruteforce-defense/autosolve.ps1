function Step-Title($text) {
    Write-Host ""
    Write-Host "===================================================="
    Write-Host $text
    Write-Host "===================================================="
}

function Show-Command($cmd) {
    Write-Host ""
    Write-Host "Command:"
    Write-Host $cmd
    Write-Host ""
    Write-Host "Output:"
}

Step-Title "CYBERARCADE AUTOSOLVE: SSH BRUTE FORCE DEFENSE"

Write-Host "In this scenario, the attacker used Hydra to brute-force SSH."
Write-Host "We will defend the target using Fail2Ban."
Write-Host "Fail2Ban watches failed SSH logins and bans repeated attackers."

Step-Title "STEP 1: Check SSH is running on the target"

Show-Command "service ssh status"

docker exec cyber_target bash -c "service ssh status || true"

Step-Title "STEP 2: Create the Fail2Ban jail configuration file"

Write-Host "We will create this file:"
Write-Host "/etc/fail2ban/jail.local"

Show-Command "cat > /etc/fail2ban/jail.local"

docker exec cyber_target bash -c "cat > /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 600
findtime = 600
EOF"

Write-Host ""
Write-Host "File created successfully."

Step-Title "STEP 3: Show the file content"

Show-Command "cat /etc/fail2ban/jail.local"

docker exec cyber_target bash -c "cat /etc/fail2ban/jail.local"

Step-Title "STEP 4: Explain the configuration"

Write-Host "enabled = true  -> turns on protection for SSH"
Write-Host "port = ssh      -> protects the SSH service"
Write-Host "filter = sshd   -> uses SSH login failure patterns"
Write-Host "logpath         -> tells Fail2Ban where SSH logs are"
Write-Host "maxretry = 3    -> ban after 3 failed attempts"
Write-Host "bantime = 600   -> ban attacker for 10 minutes"
Write-Host "findtime = 600  -> count failures within 10 minutes"

Step-Title "STEP 5: Restart Fail2Ban"

Show-Command "service fail2ban restart"

docker exec cyber_target bash -c "service fail2ban restart"

Step-Title "STEP 6: Verify Fail2Ban is protecting SSH"

Show-Command "fail2ban-client status sshd"

docker exec cyber_target bash -c "fail2ban-client status sshd"

Step-Title "AUTOSOLVE COMPLETE"

Write-Host "The target is now protected."
Write-Host "Students learned the command, the file created, the content, and the verification."