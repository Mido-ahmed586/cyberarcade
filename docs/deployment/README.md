# Deployment Guide

## Local Development

See the [Quick Start](../../README.md#getting-started) section in the main README.

---

## Docker Compose Production Deployment

### Recommended Server Specification

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 40 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Docker | 24.0+ | Latest stable |

### Steps

```bash
# 1. Clone on the server
git clone https://github.com/Mido-ahmed586/cyberarcade.git
cd cyberarcade

# 2. Configure environment
cp .env.example .env
nano .env  # Set SECRET_KEY, DB passwords, domain names

# 3. Build and start
docker compose -f docker-compose.yml up -d --build

# 4. Seed initial data
docker exec cyberarcade-backend-1 python seeds/seed_all.py

# 5. Verify
docker compose ps
curl http://localhost:8000/health
```

---

## Reverse Proxy (nginx + TLS)

Place nginx in front of both the backend and frontend for TLS termination.

```nginx
server {
    listen 443 ssl;
    server_name cyberarcade.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/cyberarcade.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cyberarcade.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support for Guacamole
    location /guacamole/ {
        proxy_pass http://localhost:8080/guacamole/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Obtain a certificate with Certbot:
```bash
sudo certbot --nginx -d cyberarcade.yourdomain.com
```

---

## Post-Deployment Checklist

- [ ] All default passwords changed
- [ ] TLS certificate installed and auto-renewing
- [ ] `SECRET_KEY` is a strong random value
- [ ] Database has regular automated backups
- [ ] Firewall rules: only ports 80/443 exposed externally
- [ ] Docker daemon not accessible from outside the host
- [ ] Log aggregation configured
- [ ] Monitoring / uptime alerts configured
