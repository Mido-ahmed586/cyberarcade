# Contributing to CyberArcade

Thank you for your interest in contributing to CyberArcade. This document describes how to get involved, what we expect from contributors, and how the review process works.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Branch Naming](#branch-naming)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Security Vulnerabilities](#security-vulnerabilities)

---

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to maintain a respectful, inclusive environment.

---

## Ways to Contribute

| Contribution Type | How |
|---|---|
| Bug fix | Open an issue → discuss → submit PR |
| New feature | Open a feature request issue first |
| Documentation | Edit docs/ or inline docstrings |
| Lab scenario | Follow the Lab Scenario Guide below |
| Translation | Open an issue to discuss |
| Security report | See [SECURITY.md](SECURITY.md) — do not use public issues |

---

## Development Setup

### Prerequisites

- Docker Desktop 24.0+
- Python 3.11+
- Node.js 18+
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/cyberarcade.git
cd cyberarcade
git remote add upstream https://github.com/Mido-ahmed586/cyberarcade.git
```

### Backend Setup

```bash
cd backend/cyberarcade-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Edit .env with your local config
alembic stamp head
python seeds/seed_all.py
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend/cyberarcade
npm install
npm run dev
```

---

## Branch Naming

Use the following naming convention:

| Prefix | Use for |
|---|---|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `refactor/` | Code restructuring without behaviour change |
| `test/` | Adding or fixing tests |
| `chore/` | Build scripts, CI, dependencies |

Examples:
```
feat/multiplayer-labs
fix/guacamole-auth-timeout
docs/api-reference-update
chore/upgrade-fastapi-0.110
```

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(labs): add VNC support to Guacamole gateway
fix(auth): resolve JWT expiry not being enforced on /me endpoint
docs(api): add examples to lab runtime endpoints
chore(deps): upgrade SQLAlchemy to 2.0.x
```

---

## Pull Request Process

1. **Create an issue first** for anything beyond a trivial bug fix. Discuss the approach before writing code.
2. **Keep PRs focused.** One feature or fix per PR. Large PRs are harder to review and slower to merge.
3. **Write tests** for new functionality where applicable.
4. **Update documentation** — docstrings, README sections, or docs/ pages if your change affects public behaviour.
5. **Ensure CI passes** before requesting review. All checks must be green.
6. **Request review** from a maintainer. Address feedback promptly.
7. **Do not squash** commits yourself — maintainers will squash on merge if needed.

### PR Title Format

Follow the same Conventional Commits format as commit messages:
```
feat(instructor): add bulk student enrollment API
fix(labs): prevent container leak on abrupt session close
```

---

## Code Standards

### Python (Backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Type hints on all function signatures
- Pydantic models for all request/response schemas
- No raw SQL — use SQLAlchemy ORM
- Maximum line length: 100 characters
- Docstrings on public functions and classes

```python
# Good
async def get_lab(lab_id: int, db: AsyncSession) -> Lab:
    """Retrieve a lab by ID. Raises 404 if not found."""
    result = await db.execute(select(Lab).where(Lab.lab_id == lab_id))
    lab = result.scalar_one_or_none()
    if lab is None:
        raise HTTPException(status_code=404, detail="Lab not found")
    return lab
```

### JavaScript / React (Frontend)

- Functional components with hooks only (no class components)
- Descriptive variable and function names
- No inline styles — use CSS modules or existing class system
- PropTypes or TypeScript interfaces for component props

### Docker / Infrastructure

- Pin base image versions (e.g., `postgres:15-alpine` not `postgres:latest`)
- Minimise image layers
- Never store secrets in Dockerfiles or images
- Use `.dockerignore` to exclude development files

---

## Testing

### Backend Tests

```bash
cd backend/cyberarcade-backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend/cyberarcade
npm test
npm run test:coverage
```

### Running Full Test Suite

```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Adding a Lab Scenario

Lab scenarios live in `scenarios/`. Each scenario is a self-contained Docker Compose stack.

**Structure:**
```
scenarios/your-scenario-name/
├── docker-compose.yml
├── Dockerfile.guacamole
├── guacamole/
│   └── user-mapping.xml
├── kali/
│   └── Dockerfile
└── target/
    └── Dockerfile
```

**Requirements for a valid lab scenario:**
1. All services must be on a named isolated Docker bridge network
2. Guacamole must use `Dockerfile.guacamole` with `COPY guacamole/user-mapping.xml`
3. The lab must expose SSH on a unique host port
4. A corresponding runtime slug must be added to `backend/app/services/`
5. Lab tasks must have `expected_answer` and at least one hint

---

## Reporting Bugs

Use the [Bug Report](https://github.com/Mido-ahmed586/cyberarcade/issues/new?template=bug_report.yml) issue template.

Include:
- Platform version and commit hash
- Steps to reproduce (minimal, exact)
- Expected vs. actual behaviour
- Docker version and OS
- Relevant log output

---

## Suggesting Features

Use the [Feature Request](https://github.com/Mido-ahmed586/cyberarcade/issues/new?template=feature_request.yml) issue template.

Before submitting, search existing issues to avoid duplicates. Describe the problem you're trying to solve, not just the solution.

---

## Security Vulnerabilities

Do **not** open a public GitHub issue for security vulnerabilities.

Follow the process described in [SECURITY.md](SECURITY.md).
