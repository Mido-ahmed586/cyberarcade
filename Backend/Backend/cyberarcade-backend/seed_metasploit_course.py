"""
Seed script: Metasploit & Metasploitable Penetration Testing course.
TryHackMe-style: each task has educational context before the question.

Run from the cyberarcade-backend directory (venv activated):
    python seed_metasploit_course.py

Idempotent: deletes existing course with the same title before re-seeding.
"""
import asyncio
from uuid import UUID
from sqlalchemy import delete, select
from app.core.database import async_session
from app.models.course import Course, Module
from app.models.lab import Lab, LabTask, Hint

SEED_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
COURSE_TITLE = "Metasploit & Metasploitable Penetration Testing"

# ── Lab 0 — Theory (no terminal) ───────────────────────────────────────────────
LAB0_TASKS = [
    (
        "What does CVE stand for?",
        """\
**Common Vulnerabilities and Exposures (CVE)** is the global standard for identifying and naming publicly known cybersecurity vulnerabilities.

Each CVE entry has a unique ID in the format **CVE-YEAR-NUMBER** (e.g., `CVE-2021-44228` is the famous Log4Shell vulnerability). The list is maintained by **MITRE Corporation** and is used by security tools, vulnerability scanners, and patch management systems worldwide.

When a researcher discovers a vulnerability, they request a CVE ID so the community can track it consistently — the same vulnerability gets the same name regardless of which vendor or tool refers to it.

> **Famous examples:** CVE-2017-0144 (EternalBlue / WannaCry), CVE-2021-44228 (Log4Shell), CVE-2014-0160 (Heartbleed)

What does the acronym **CVE** stand for?""",
        "Common Vulnerabilities and Exposures",
        [],
        [
            "CVE is maintained by MITRE Corporation.",
            "Three words: Common, Vulnerabilities, and Exposures.",
        ],
    ),
    (
        "What is the first phase of a penetration test?",
        """\
A penetration test follows a structured methodology with distinct phases. Understanding the order matters — skipping phases leads to missed vulnerabilities or noisy attacks that get detected.

**The five phases of a penetration test:**

1. **Reconnaissance** — Gather information about the target (passive and active)
2. **Scanning & Enumeration** — Discover open ports, services, and versions
3. **Exploitation** — Leverage vulnerabilities to gain access
4. **Post-Exploitation** — Escalate privileges, pivot, maintain persistence
5. **Reporting** — Document findings and remediation steps

The very first phase is passive — you collect publicly available information without directly touching the target. This includes WHOIS lookups, DNS enumeration, LinkedIn profiling, and more.

What is the **first phase** of a penetration test?""",
        "reconnaissance",
        [],
        [
            "This phase is also called 'information gathering' or 'footprinting'.",
            "The term starts with the letter R.",
        ],
    ),
    (
        "What is the default port for MySQL?",
        """\
Every network service listens on a **port number** — a 16-bit number (0–65535) that identifies which service should handle incoming traffic. Knowing default ports is essential for both attackers and defenders.

**Common default ports you must know:**

| Port | Service |
|------|---------|
| 21   | FTP     |
| 22   | SSH     |
| 80   | HTTP    |
| 443  | HTTPS   |
| 3306 | ?       |
| 5432 | PostgreSQL |
| 27017 | MongoDB |

Metasploitable2 exposes many of these. During our Nmap lab you will see them all.

What is the **default TCP port** for MySQL?""",
        "3306",
        [],
        [
            "The port number is between 3000 and 4000.",
        ],
    ),
    (
        "What Metasploit command searches for modules?",
        """\
**Metasploit Framework** is the world's most widely used penetration testing platform. Its interactive console, `msfconsole`, gives you access to thousands of exploits, payloads, auxiliary scanners, and post-exploitation modules.

**The basic Metasploit workflow:**

```
msfconsole          # start the console
search <keyword>    # find modules
use <module_path>   # select a module
info                # read module details
set RHOSTS <ip>     # configure the target
set LHOST <ip>      # configure your listener
run                 # launch the exploit
```

Before you can exploit anything you need to find the right module. Metasploit has over 2,000 exploits — the `search` command filters them by keyword, CVE ID, or platform.

**Example:** `search unreal_ircd` will find the UnrealIRCd backdoor exploit we will use later in this course.

What single-word msfconsole command do you use to **search for modules**?""",
        "search",
        [],
        [
            "It's the same word you type into Google every day.",
        ],
    ),
    (
        "What does CVSS stand for?",
        """\
Knowing a vulnerability exists is only half the story — you also need to understand **how severe** it is. That's what **CVSS** (Common Vulnerability Scoring System) is for.

CVSS rates vulnerabilities on a **0.0 – 10.0 scale** based on factors like:
- **Attack Vector** — Network, adjacent, local, or physical?
- **Attack Complexity** — Is it easy or hard to exploit?
- **Privileges Required** — Does the attacker need existing credentials?
- **Impact** — How badly is confidentiality, integrity, or availability affected?

**CVSS severity ranges:**

| Score   | Severity |
|---------|----------|
| 0.0     | None     |
| 0.1–3.9 | Low      |
| 4.0–6.9 | Medium   |
| 7.0–8.9 | High     |
| 9.0–10.0 | **Critical** |

The vulnerabilities in Metasploitable2 include several **Critical (9.0+)** CVEs — you will exploit two of them in this course.

What does **CVSS** stand for?""",
        "Common Vulnerability Scoring System",
        [],
        [
            "CVSS scores of 9–10 are labelled 'Critical'.",
            "Four words: Common, Vulnerability, Scoring, System.",
        ],
    ),
]

# ── Lab 1 — Network Reconnaissance with Nmap ──────────────────────────────────
LAB1_TASKS = [
    (
        "How many open TCP ports does Metasploitable2 have?",
        """\
**Nmap** (Network Mapper) is the most widely used port scanner in the world. It discovers live hosts, open ports, running services, and operating systems across a network.

**Launch your terminal** by clicking **Launch Machine** below, then try your first scan:

```
nmap --open -T4 metasploitable2
```

**What these flags mean:**
- `--open` — only show ports that are open (filters out closed/filtered)
- `-T4` — aggressive timing (faster scan, fine in a lab)
- `metasploitable2` — the target hostname (resolvable inside this lab network)

You should see a list of open TCP ports. Count them up — Metasploitable2 is intentionally vulnerable and exposes many services.

**How many open TCP ports** does the default Nmap scan find?""",
        "11",
        [
            "nmap --open -T4 metasploitable2 2>/dev/null",
            "nmap --open -T4 metasploitable2 2>/dev/null | grep -c '^[0-9]*/tcp'",
        ],
        [
            "Use the `--open` flag so only open ports are shown.",
            "Pipe through `grep -c '^[0-9]*/tcp'` to count the lines automatically.",
        ],
    ),
    (
        "What SSH version is running on port 22?",
        """\
A basic port scan tells you which ports are open, but not what software is running on them. The **`-sV` flag** (service version detection) makes Nmap probe each open port and identify the exact software and version.

Run this command in your terminal:

```
nmap -sV -p 22 metasploitable2
```

**What `-sV -p 22` means:**
- `-sV` — enable service/version detection
- `-p 22` — scan only port 22 (SSH)

In the output, look for a line like:
```
22/tcp  open  ssh   <software> <version>
```

Knowing the exact SSH version is important — older versions have known exploits. For example, **OpenSSH 4.7** was released in 2007 and has several vulnerabilities.

What is the **SSH software and version** running on port 22? (format: `OpenSSH X.Yp1`)""",
        "OpenSSH 4.7p1",
        [
            "nmap -sV -p 22 metasploitable2 2>/dev/null | grep '22/tcp'",
            "nmap -sV -p 22 metasploitable2 2>/dev/null | grep -oP 'OpenSSH [0-9.p]+'",
        ],
        [
            "Use `nmap -sV -p 22 metasploitable2` to scan just port 22.",
            "The answer format is 'OpenSSH X.Yp1' — include the 'p1' suffix.",
        ],
    ),
    (
        "What web server is running on port 80?",
        """\
Port 80 is the default port for HTTP (unencrypted web traffic). Identifying the web server software and version is a key step — different versions have different vulnerabilities.

Run:
```
nmap -sV -p 80 metasploitable2
```

In the output, look for the `80/tcp` line. The web server name and version will appear after the protocol label.

**Why this matters:** Apache httpd 2.2.8 was released in 2008. Older Apache versions can be vulnerable to path traversal, buffer overflows, and configuration weaknesses. Metasploitable2 intentionally runs old, vulnerable software.

What is the **web server software and version** on port 80? (format: `Apache httpd X.Y.Z`)""",
        "Apache httpd 2.2.8",
        [
            "nmap -sV -p 80 metasploitable2 2>/dev/null | grep '80/tcp'",
            "nmap -sV -p 80 metasploitable2 2>/dev/null | grep -oP 'Apache httpd [0-9.]+'",
        ],
        [
            "Use `nmap -sV -p 80 metasploitable2` to scan port 80.",
            "The answer starts with 'Apache httpd' followed by the version number.",
        ],
    ),
    (
        "What MySQL version is running on port 3306?",
        """\
Now scan the database port. MySQL is one of the most common database servers, and knowing its version helps identify applicable exploits.

```
nmap -sV -p 3306 metasploitable2
```

Look for the `3306/tcp` line. You will see the MySQL version reported by Nmap's service probes.

**Why this matters:** MySQL 5.0.x has several known vulnerabilities including privilege escalation and information disclosure issues. In real engagements, a discovered database port is always a high-priority target.

What is the **MySQL version** on port 3306? (format: `MySQL X.Y.ZZ`)""",
        "MySQL 5.0.51a",
        [
            "nmap -sV -p 3306 metasploitable2 2>/dev/null | grep '3306/tcp'",
            "nmap -sV -p 3306 metasploitable2 2>/dev/null | grep -oP 'MySQL [0-9.a]+'",
        ],
        [
            "Use `nmap -sV -p 3306 metasploitable2`.",
            "The version starts with `5.0` and has a letter suffix.",
        ],
    ),
    (
        "What IRC service is running on port 6667?",
        """\
Port 6667 is the default port for **IRC (Internet Relay Chat)** — a protocol from the 1980s still used today. Metasploitable2 runs a specific IRC server on this port that contains a **critical backdoor vulnerability** (CVE-2010-2075).

Scan it:
```
nmap -sV -p 6667 metasploitable2
```

Look for the service name on the `6667/tcp` line.

**Background:** In 2009, an attacker compromised the UnrealIRCd source code distribution server and inserted a backdoor. Anyone who downloaded that version unknowingly ran malicious code. This is called a **supply-chain attack** — the software itself was weaponised before distribution.

We will exploit this backdoor in a later lab using Metasploit's `exploit/unix/irc/unreal_ircd_3281_backdoor` module.

What is the **IRC service name** running on port 6667?""",
        "UnrealIRCd",
        [
            "nmap -sV -p 6667 metasploitable2 2>/dev/null | grep '6667/tcp'",
            "nmap -sV -p 6667 metasploitable2 2>/dev/null | grep -oP 'UnrealIRCd'",
        ],
        [
            "The service has a known backdoor vulnerability (CVE-2010-2075).",
            "The answer is a single word.",
        ],
    ),
]

# ── Lab 2 — Service Enumeration & Banner Grabbing ─────────────────────────────
LAB2_TASKS = [
    (
        "What PHP version is the web server running?",
        """\
HTTP response headers often leak server-side technology information — a goldmine for attackers during enumeration. The `curl -I` command fetches **only the headers** (no body), quickly revealing web server details.

Run in your terminal:
```
curl -s -I http://metasploitable2/
```

Scan through the headers. You are looking for the **`X-Powered-By`** header, which web applications use to advertise the scripting language they run on.

**Example header output:**
```
HTTP/1.1 200 OK
Server: Apache/2.2.8 (Ubuntu)
X-Powered-By: PHP/x.x.x
```

What is the **full value** of the `X-Powered-By` header? (format: `PHP/X.Y.Z-...`)""",
        "PHP/5.2.4-2ubuntu5.10",
        [
            "curl -s -I http://metasploitable2/ 2>/dev/null | grep -i 'X-Powered-By'",
            "curl -s -I http://metasploitable2/ 2>/dev/null | grep -oP 'PHP/[0-9.\\-a-z]+'",
        ],
        [
            "Use `curl -I http://metasploitable2/` to fetch HTTP headers only.",
            "Look for the `X-Powered-By` header — it contains the PHP version.",
        ],
    ),
    (
        "What is the title of the Metasploitable2 web page?",
        """\
The HTML `<title>` tag contains the page title shown in the browser tab. For enumeration, it confirms you've reached the right target and can reveal application names or environments.

Fetch the page source and extract the title:
```
curl -s http://metasploitable2/ | grep -oP '(?<=<title>)[^<]+'
```

**What this command does:**
- `curl -s http://metasploitable2/` — silently fetch the HTML
- `grep -oP '(?<=<title>)[^<]+'` — extract only the text between `<title>` and `</title>`

What is the **exact page title** of the Metasploitable2 default web page?""",
        "Metasploitable2 - Linux",
        [
            "curl -s http://metasploitable2/ 2>/dev/null | grep -oP '(?<=<title>)[^<]+'",
        ],
        [
            "Use `curl -s http://metasploitable2/` to get the page source.",
            "The title is inside an HTML `<title>` tag.",
        ],
    ),
    (
        "What VNC protocol version is running on port 5900?",
        """\
**VNC (Virtual Network Computing)** enables remote desktop access. Port 5900 is the standard VNC port. If VNC is exposed without authentication (or with a weak password), an attacker can take full graphical control of the machine.

Scan it with Nmap:
```
nmap -sV -p 5900 metasploitable2
```

The output will identify the VNC software and the **protocol version** it supports. Older protocol versions (like 3.3) offer weaker security.

What is the VNC service description on port 5900? (format: `VNC (protocol X.X)`)""",
        "VNC (protocol 3.3)",
        [
            "nmap -sV -p 5900 metasploitable2 2>/dev/null | grep '5900/tcp'",
            "nmap -sV -p 5900 metasploitable2 2>/dev/null | grep -oP 'VNC \\(protocol [0-9.]+\\)'",
        ],
        [
            "Use `nmap -sV -p 5900 metasploitable2`.",
            "The answer includes 'protocol' in parentheses — e.g., `VNC (protocol X.X)`.",
        ],
    ),
    (
        "What Samba version range is advertised on port 445?",
        """\
**Samba** implements the SMB (Server Message Block) protocol on Linux, allowing Windows-style file and printer sharing. Port 445 is the primary SMB port.

Metasploitable2 runs an ancient version of Samba that is vulnerable to **CVE-2007-2447**, a critical remote code execution vulnerability known as the **"username map script"** exploit — one of the easiest exploits in Metasploit.

Scan port 445:
```
nmap -sV -p 445 metasploitable2
```

Nmap will report a version range for the Samba service on this port.

What is the **Samba version range** reported by Nmap? (format: `Samba smbd X.X - Y.Y`)""",
        "Samba smbd 3.X - 4.X",
        [
            "nmap -sV -p 445 metasploitable2 2>/dev/null | grep '445/tcp'",
            "nmap -sV -p 445 metasploitable2 2>/dev/null | grep -oP 'Samba smbd [0-9X. -]+'",
        ],
        [
            "Use `nmap -sV -p 445 metasploitable2`.",
            "The answer is in the format `Samba smbd X.X - Y.Y` using 'X' for the major version placeholders.",
        ],
    ),
    (
        "What type of vulnerability affects UnrealIRCd on Metasploitable2?",
        """\
Now that you have identified UnrealIRCd on port 6667, let's understand the vulnerability.

**CVE-2010-2075** is a supply-chain attack: in 2009, an attacker compromised the UnrealIRCd distribution server and inserted malicious code into the source tarball. The backdoor allows **remote command execution** — an attacker can send a specially crafted string to port 6667 that triggers the execution of arbitrary OS commands with the privileges of the IRC server process.

**Attack flow:**
1. Connect to port 6667
2. Send: `AB;` followed by a shell command
3. The backdoor executes the command on the server

This vulnerability has a Metasploit module (`exploit/unix/irc/unreal_ircd_3281_backdoor`) that automates the entire attack. You will use it in the next lab.

What type of vulnerability is CVE-2010-2075 classified as? Enter: **backdoor command execution**""",
        "backdoor command execution",
        [],
        [
            "This was a supply-chain attack — malicious code was inserted into a legitimate release.",
            "The answer is three words describing what the backdoor does.",
        ],
    ),
]

# ── Lab 3 — Exploitation with Metasploit ──────────────────────────────────────
LAB3_TASKS = [
    (
        "What is the msfconsole command to select a module?",
        """\
You have identified two critical vulnerabilities on Metasploitable2:
- **CVE-2010-2075** — UnrealIRCd backdoor (port 6667)
- **CVE-2007-2447** — Samba username map script (port 445)

Now it's time to exploit them using **Metasploit**.

**The core Metasploit workflow:**

```
# 1. Search for the module
search unreal_ircd

# 2. Select it
use exploit/unix/irc/unreal_ircd_3281_backdoor

# 3. Configure it
set RHOSTS metasploitable2
set LHOST <your IP>

# 4. Verify options
show options

# 5. Launch
run
```

The command used in **step 2** — selecting a module — is a single word followed by the full module path.

What is the **msfconsole command** used to select a module? (single word)""",
        "use",
        [],
        [
            "After this command you type the full module path, e.g. `use exploit/unix/irc/unreal_ircd_3281_backdoor`.",
        ],
    ),
    (
        "What Metasploit option sets the target IP?",
        """\
Every Metasploit exploit requires at minimum two pieces of information: the **target** (remote host) and your **listener** (local host). These are set as module options.

**Key options in most exploits:**

| Option   | Meaning                        |
|----------|-------------------------------|
| `RHOSTS` | Remote host(s) — the target   |
| `RPORT`  | Remote port — target's port   |
| `LHOST`  | Local host — your IP          |
| `LPORT`  | Local port — your listener    |

You configure these with `set <OPTION> <value>`:
```
set RHOSTS metasploitable2
set LHOST 0.0.0.0
```

After setting options you can verify them with `show options` — this lists required and optional settings and whether they are configured.

What is the **option name** used to specify the **target IP address**?""",
        "RHOSTS",
        [],
        [
            "The option name starts with R (for Remote).",
            "LHOST is your attacker IP; the *remote* host option starts with RH.",
        ],
    ),
    (
        "What msfconsole command shows module details?",
        """\
Before running an exploit it is good practice to read its documentation. Metasploit includes detailed information for every module including:
- A description of the vulnerability it exploits
- The CVE references
- Required and optional options
- Author and reliability rating

You access this with a single-word command inside msfconsole (after selecting a module with `use`):

```
use exploit/unix/irc/unreal_ircd_3281_backdoor
info
```

The output will show you everything about the module — including that this exploit targets **CVE-2010-2075** and reliably gives a shell on the target.

What single-word msfconsole command **shows detailed module information**?""",
        "info",
        [],
        [
            "It's a common English word meaning 'information'.",
        ],
    ),
    (
        "What Metasploit module exploits the UnrealIRCd backdoor?",
        """\
Now search for the UnrealIRCd exploit module. Inside msfconsole, run:

```
search unreal_ircd
```

You will see a table of matching modules. Find the **exploit** module (not auxiliary or post) that targets the UnrealIRCd backdoor. The module path follows the Metasploit naming convention:

```
<type>/<platform>/<service>/<module_name>
```

For example: `exploit/unix/irc/<name>`

**Auto-Solve note:** The auto-solve will run this search in your terminal and extract the module path automatically.

What is the **full module path** for the UnrealIRCd backdoor exploit?""",
        "exploit/unix/irc/unreal_ircd_3281_backdoor",
        [
            "msfconsole -q -x 'search unreal_ircd; exit' 2>/dev/null | grep unreal_ircd | grep exploit | awk '{print $2}'",
        ],
        [
            "Run `search unreal_ircd` inside msfconsole.",
            "The module path follows: `exploit/unix/irc/<name>`.",
        ],
    ),
    (
        "What Metasploit module exploits the Samba vulnerability?",
        """\
The second critical vulnerability is in Samba — **CVE-2007-2447**, known as the "username map script" vulnerability. It allows unauthenticated remote code execution by injecting shell commands into the Samba username field.

Search for it in msfconsole:
```
search usermap_script
```

Find the **exploit** module in the results. The module path follows the pattern:
```
exploit/multi/samba/<name>
```

Once you find it, you can exploit Metasploitable2's Samba service with just three commands:
```
use exploit/multi/samba/usermap_script
set RHOSTS metasploitable2
run
```

This gives you a **root shell** — no password required. That's the power (and danger) of unpatched, vulnerable services.

What is the **full module path** for the Samba usermap_script exploit?""",
        "exploit/multi/samba/usermap_script",
        [
            "msfconsole -q -x 'search usermap_script; exit' 2>/dev/null | grep usermap_script | grep exploit | awk '{print $2}'",
        ],
        [
            "Run `search usermap_script` inside msfconsole.",
            "The module path starts with `exploit/multi/samba/`.",
        ],
    ),
]

MODULE_CONTENT = """\
## Introduction to Metasploit and Metasploitable2

### What is Metasploitable2?
Metasploitable2 is an intentionally vulnerable Linux virtual machine designed for practising penetration testing techniques. It runs a range of deliberately insecure services that mirror real-world vulnerabilities found in older production systems.

### What is Metasploit Framework?
Metasploit is the world's most widely used penetration testing framework. It provides:
- **Exploits**: code that takes advantage of a vulnerability
- **Payloads**: code executed on the target after exploitation (shells, Meterpreter, etc.)
- **Auxiliary modules**: scanners, fuzzers, and other recon tools
- **Post modules**: post-exploitation actions (persistence, pivot, etc.)

### Lab Network
In this course the Metasploitable2 target is reachable from your Kali terminal at hostname `metasploitable2`. No external internet access is required.

### Safety Note
All activities in this course are performed in an isolated Docker network. Never run these techniques against systems you do not own or have explicit written permission to test."""


async def delete_existing(db):
    result = await db.execute(select(Course).where(Course.title == COURSE_TITLE))
    existing = result.scalar_one_or_none()
    if existing:
        await db.execute(delete(Course).where(Course.course_id == existing.course_id))
        await db.commit()
        print(f"Deleted existing course: {COURSE_TITLE}")


async def seed():
    async with async_session() as db:
        await delete_existing(db)

        course = Course(
            title=COURSE_TITLE,
            created_by=SEED_USER_ID,
            description=(
                "Learn penetration testing fundamentals using the Metasploit Framework "
                "against the intentionally vulnerable Metasploitable2 target. Covers "
                "network reconnaissance with Nmap, service enumeration, vulnerability "
                "identification, and exploitation using real Metasploit modules — all "
                "inside a safe, isolated Docker lab environment."
            ),
            difficulty_level="intermediate",
            category="Penetration Testing",
            estimated_hours=8,
            is_published=True,
        )
        db.add(course)
        await db.flush()
        print(f"Created course: {course.title}  [{course.course_id}]")

        module = Module(
            course_id=course.course_id,
            title="Metasploit & Metasploitable2 Fundamentals",
            content=MODULE_CONTENT,
            sort_order=1,
        )
        db.add(module)
        await db.flush()

        async def add_lab(title, description, difficulty, runtime_slug, sort_order, task_defs):
            docker_cfg = (
                {"runtime_slug": runtime_slug, "terminal_type": "single"}
                if runtime_slug else {}
            )
            lab = Lab(
                course_id=course.course_id,
                module_id=module.module_id,
                title=title,
                description=description,
                difficulty=difficulty,
                docker_compose_config=docker_cfg,
                has_auto_solve=any(cmds for _, _, _, cmds, _ in task_defs),
                max_duration_minutes=120,
                sort_order=sort_order,
                is_published=True,
            )
            db.add(lab)
            await db.flush()
            print(f"  Lab [{sort_order}]: {title}  [{lab.lab_id}]")

            for i, (t_title, t_instr, t_answer, t_cmds, t_hints) in enumerate(task_defs, 1):
                task = LabTask(
                    lab_id=lab.lab_id,
                    title=t_title,
                    instructions=t_instr,
                    expected_answer=t_answer,
                    autosolve_commands=t_cmds,
                    sort_order=i,
                )
                db.add(task)
                await db.flush()

                for j, hint_text in enumerate(t_hints, 1):
                    db.add(Hint(
                        task_id=task.task_id,
                        hint_text=hint_text,
                        hint_order=j,
                        delay_minutes=0,
                    ))

                print(f"    Task {i}: {t_title[:60]}")

            await db.flush()
            return lab

        await add_lab(
            title="Penetration Testing Concepts",
            description=(
                "Before touching any tools, understand the fundamentals: CVE, CVSS, "
                "penetration testing methodology, and the Metasploit command structure. "
                "No live machine required — theory only."
            ),
            difficulty="beginner",
            runtime_slug=None,
            sort_order=1,
            task_defs=LAB0_TASKS,
        )

        await add_lab(
            title="Network Reconnaissance with Nmap",
            description=(
                "Launch Nmap against Metasploitable2 to discover all open ports and "
                "identify running services with version detection. This is the "
                "reconnaissance phase of a real penetration test."
            ),
            difficulty="intermediate",
            runtime_slug="metasploit",
            sort_order=2,
            task_defs=LAB1_TASKS,
        )

        await add_lab(
            title="Service Enumeration & Banner Grabbing",
            description=(
                "Go deeper into discovered services using curl and Nmap banner grabbing "
                "to extract PHP version, web titles, VNC protocol, Samba version, and "
                "identify exploitable vulnerabilities."
            ),
            difficulty="intermediate",
            runtime_slug="metasploit",
            sort_order=3,
            task_defs=LAB2_TASKS,
        )

        await add_lab(
            title="Exploitation with Metasploit",
            description=(
                "Learn the Metasploit workflow: search, use, set, info, run. "
                "Identify the exact exploit modules for UnrealIRCd (CVE-2010-2075) "
                "and Samba (CVE-2007-2447) ready to fire in your next session."
            ),
            difficulty="intermediate",
            runtime_slug="metasploit",
            sort_order=4,
            task_defs=LAB3_TASKS,
        )

        await db.commit()
        print(f"\nDone. Course '{COURSE_TITLE}' seeded with 4 labs and 20 tasks.")


if __name__ == "__main__":
    asyncio.run(seed())
