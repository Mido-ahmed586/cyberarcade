# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `main` branch | Yes — active development |
| Tagged releases | Yes — latest two minor versions |
| Older releases | No — upgrade recommended |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.** Public disclosure before a fix is available puts all platform users at risk.

### How to Report

Send a detailed vulnerability report to:

**Email:** `security@cyberarcade.io` *(replace with your actual contact)*

Or use [GitHub's private vulnerability reporting](https://github.com/Mido-ahmed586/cyberarcade/security/advisories/new) feature.

### What to Include

Please provide as much of the following as possible:

- **Description** of the vulnerability and its potential impact
- **Affected component** (backend, frontend, lab container, Guacamole integration)
- **Steps to reproduce** — minimal, precise reproduction steps
- **Proof of concept** — code, curl commands, or screenshots (no live exploitation)
- **Suggested fix** (optional but appreciated)
- **Your contact information** for follow-up

### What to Expect

| Step | Timeline |
|---|---|
| Acknowledgement of receipt | Within 48 hours |
| Initial triage and severity assessment | Within 5 business days |
| Patch development and testing | Depends on severity (1–30 days) |
| Credit and coordinated disclosure | On patch release |

We follow a **90-day responsible disclosure** policy. If we cannot resolve a reported issue within 90 days, we will notify you and coordinate public disclosure timing.

---

## Security Architecture

### Authentication

- JWT tokens (HS256) with configurable expiry
- Passwords hashed with bcrypt (work factor 12)
- No plaintext credential storage anywhere in the codebase
- Rate limiting on `/auth/login` and `/auth/register`

### Authorisation

- Role-Based Access Control: `student`, `instructor`, `admin`
- Route-level permission guards enforced server-side
- Resource ownership checks — students cannot access other students' data

### Container Security

- Each lab runs in an isolated Docker bridge network
- No lab container can reach the host network or other lab networks
- `NET_RAW` and `NET_ADMIN` capabilities granted only where required (Nmap scanning)
- Lab containers are torn down after session close
- No secrets are baked into lab container images

### API Security

- All inputs validated via Pydantic models before processing
- SQL injection prevented by SQLAlchemy ORM (no raw queries)
- CORS policy restricted to configured allowed origins
- File paths sanitised — no directory traversal
- Command injection: `subprocess` calls use list arguments (no `shell=True`)

### Network Security

- Lab scenario stacks run on private Docker subnets (172.25.0.0/24 – 172.31.0.0/24)
- Apache Guacamole acts as a proxied terminal gateway — students never get direct SSH access from outside
- Production deployments should place the platform behind a reverse proxy (nginx) with TLS

---

## Production Hardening Checklist

Before deploying CyberArcade in a public-facing or institutional environment:

- [ ] Change all default passwords (`admin@cyberarcade.io`, `guacadmin`, lab SSH credentials)
- [ ] Set a strong, random `SECRET_KEY` in `.env`
- [ ] Configure TLS with a valid certificate (Let's Encrypt recommended)
- [ ] Restrict CORS to your specific domain
- [ ] Enable database connection encryption
- [ ] Set up regular PostgreSQL backups
- [ ] Configure Docker daemon to run without privileged mode
- [ ] Apply OS-level firewall rules to expose only ports 80/443
- [ ] Enable log aggregation and alerting for authentication failures
- [ ] Rotate JWT secret keys on a regular schedule

---

## Known Limitations

The following limitations are known and accepted for the current release scope:

- Lab containers run as `root` inside the container (standard for Kali Linux labs). This is isolated by Docker network and namespace boundaries.
- Guacamole uses XML-based user mapping (file auth). For production multi-tenant deployments, consider migrating to Guacamole's PostgreSQL auth extension.
- The platform currently does not enforce lab session timeouts at the container level — sessions are manually terminated by the student or instructor.

---

## Scope

### In Scope

- Authentication and session management
- API endpoint authorisation bypasses
- Container escape or cross-lab network access
- SQL injection or data exfiltration
- SSRF, XXE, or command injection in any component
- Sensitive data exposure in API responses or logs

### Out of Scope

- Vulnerabilities in intentionally vulnerable lab targets (Metasploitable2, etc.)
- Denial-of-service attacks requiring significant resources
- Social engineering
- Issues already publicly disclosed
- Vulnerabilities in third-party dependencies with no CyberArcade-specific exploit path

---

## Hall of Fame

Responsible security researchers who have reported valid vulnerabilities will be acknowledged here with their permission.

*No reports yet — be the first.*
