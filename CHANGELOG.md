# Changelog

All notable changes to CyberArcade are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- CTF Event Mode
- Multiplayer lab support
- AI personalization engine
- Advanced analytics dashboard

---

## [1.0.0] — 2025-05-31

### Added

**Platform Core**
- Full-stack cybersecurity training platform with React frontend and FastAPI backend
- PostgreSQL database with Alembic schema management
- JWT authentication with role-based access control (student, instructor, admin)
- Docker Compose orchestration for the full application stack

**Courses & Learning**
- 5 auto-seeded courses on first run:
  - Web Application Security (beginner)
  - Network Penetration Testing (intermediate)
  - Linux Privilege Escalation (intermediate)
  - Digital Forensics (intermediate, 8 labs, 69 tasks)
  - Metasploit & Metasploitable Penetration Testing (intermediate, 4 labs, 20 tasks)
- Structured labs with ordered tasks, expected answers, and validation
- Time-gated progressive hint system
- Automated lab solver (auto-solve) with tmux-based terminal execution
- AI-powered cybersecurity coach with contextual assistance

**Lab Infrastructure**
- Docker-powered isolated lab environments per scenario
- Apache Guacamole integration for browser-based terminal access
- 4 operational lab scenarios:
  - SSH Bruteforce & Defense (Kali + Target, port 8081)
  - Kali Terminal Sandbox (Kali + Target, port 8081)
  - Digital Forensics Lab (forensics Kali, port 8082)
  - Metasploit & Metasploitable2 (Kali MSF + Metasploitable2, port 8080)
- On-demand lab lifecycle: start, stop, reset, health check
- Guacamole auto-session URL generation with token injection
- Lab container network isolation (dedicated Docker bridge subnets)

**User Experience**
- Landing page with live terminal animation
- Student dashboard with progress tracking
- Course catalog with difficulty and category filtering
- Interactive lab page with task panel, hint requests, and terminal
- Leaderboard with XP rankings
- Badge and achievement system
- Certificate generation on course completion
- User profile and settings management

**Instructor Features**
- Instructor dashboard and classroom management
- Student enrollment and progress monitoring
- Course and lab publishing controls

**Admin Features**
- Admin panel with user management
- Subscription plan management
- Platform-wide statistics

**Developer Experience**
- Master seed script (`seeds/seed_all.py`) for one-command database setup
- Idempotent seeding — skips existing data, supports `--force` re-seed
- Docker socket pass-through for backend-managed lab orchestration
- `host.docker.internal` resolution for Guacamole API calls from inside containers
- Comprehensive `.env.example` configuration template

### Fixed
- Backend container path resolution for `SCENARIOS_BASE` environment variable
- Guacamole authentication using `host.docker.internal` instead of `localhost`
- Docker-in-Docker bind-mount path translation — Guacamole images now use `COPY` instead of volume mounts
- `alembic stamp head` used instead of `alembic upgrade head` to prevent duplicate table errors on first run
- `subprocess.Popen` (non-blocking) used for lab start commands to prevent HTTP timeout
- Route aliases for `single` and `dual` runtime slugs

---

## [0.9.0] — 2025-04-15

### Added
- Initial platform architecture
- Course and lab data models
- Basic authentication flow
- Docker Compose skeleton
- Guacamole proof-of-concept integration

---

[Unreleased]: https://github.com/Mido-ahmed586/cyberarcade/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Mido-ahmed586/cyberarcade/releases/tag/v1.0.0
[0.9.0]: https://github.com/Mido-ahmed586/cyberarcade/releases/tag/v0.9.0
