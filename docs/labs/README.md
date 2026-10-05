# Lab Scenario Guide

CyberArcade lab scenarios are self-contained Docker Compose stacks. Each scenario lives in `scenarios/` and is started on-demand by the backend when a student launches a lab.

---

## Existing Scenarios

| Directory | Runtime Slug | Port | Description |
|---|---|---|---|
| `ssh-bruteforce-defense/` | `single`, `dual` | 8081 | SSH brute force and defense |
| `kali-terminal/` | `single`, `dual` | 8081 | General-purpose Kali terminal |
| `df-kali/` | `df-kali` | 8082 | Digital forensics lab |
| `metasploit-basics/` | `metasploit` | 8080 | Metasploit + Metasploitable2 |

---

## Creating a New Scenario

### 1. Directory Structure

```
scenarios/your-scenario/
├── docker-compose.yml          # Defines all containers
├── Dockerfile.guacamole        # Custom Guacamole image
├── guacamole/
│   ��── user-mapping.xml        # Guacamole auth config
├── kali/
│   └── Dockerfile              # Kali Linux attacker image
└── target/                     # Optional target machine
    └── Dockerfile
```

### 2. docker-compose.yml Rules

- Use a unique named Docker bridge network
- Guacamole must use `build: { dockerfile: Dockerfile.guacamole }` (not `image:`)
- Expose Guacamole on a unique host port (check existing scenarios to avoid conflicts)
- No `external: true` on networks or volumes

### 3. Dockerfile.guacamole

```dockerfile
FROM guacamole/guacamole:latest
COPY guacamole/user-mapping.xml /etc/guacamole/user-mapping.xml
```

Always use `COPY` — do not mount `user-mapping.xml` as a volume.

### 4. user-mapping.xml

```xml
<user-mapping>
  <authorize username="guacadmin" password="guacadmin">
    <connection name="Kali Terminal">
      <protocol>ssh</protocol>
      <param name="hostname">kali</param>
      <param name="port">22</param>
      <param name="username">student</param>
      <param name="password">student123</param>
      <param name="color-scheme">white-black</param>
      <param name="font-size">14</param>
    </connection>
  </authorize>
</user-mapping>
```

### 5. Backend Runtime Service

Create `backend/cyberarcade-backend/app/services/lab_runtime_service_yourscenario.py`.

Copy an existing service file (e.g., `lab_runtime_service.py`) and update:
- `SCENARIO_DIR` path
- Container names
- SSH port numbers
- Guacamole connection name and base URL

### 6. Register Routes

Add the runtime slug to `backend/cyberarcade-backend/app/routers/labs.py` following the existing pattern.

### 7. Add to Seed Data

Add labs with `docker_compose_config: {"runtime_slug": "your-slug", "terminal_type": "single"}` in `seeds/seed_all.py`.

---

## Lab Container Requirements

| Requirement | Notes |
|---|---|
| SSH server running | Required for Guacamole SSH connection |
| `PasswordAuthentication yes` in sshd_config | Required |
| Student user created | `useradd -m -s /bin/bash student` |
| SSH started in CMD or entrypoint | `/usr/sbin/sshd -D` |
| Port 22 exposed | Within the Docker network |
