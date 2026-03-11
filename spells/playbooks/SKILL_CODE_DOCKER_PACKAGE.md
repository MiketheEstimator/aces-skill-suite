---
name: SKILL_CODE_DOCKER_PACKAGE
description: "Container blueprints ensuring offline consistency and dependency management. Use when producing Dockerfiles, docker-compose.yml, or .dockerignore files for application packaging, reproducible environments, or deployment pipelines. Triggers: 'Dockerfile', 'Docker', 'containerise', 'docker-compose', 'container image', 'package for deployment'."
---

# SKILL_CODE_DOCKER_PACKAGE — Dockerfile Skill

## Quick Reference

| Task | Section |
|------|---------|
| Dockerfile templates | [Dockerfile Templates](#dockerfile-templates) |
| Multi-stage builds | [Multi-Stage Builds](#multi-stage-builds) |
| docker-compose | [Docker Compose](#docker-compose) |
| .dockerignore | [.dockerignore](#dockerignore) |
| Build & run commands | [Build & Run](#build--run) |
| Security hardening | [Security Hardening](#security-hardening) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Dockerfile Templates

### Python Application

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Metadata
LABEL maintainer="name@email.com"
LABEL description="Application description"
LABEL version="1.0.0"

# Prevent interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install Python dependencies (separate layer for cache efficiency)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port (documentation — doesn't publish)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Node.js Application

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine

LABEL maintainer="name@email.com"

# Create non-root user
RUN addgroup --gid 1001 nodegroup \
 && adduser  --uid 1001 --ingroup nodegroup --disabled-password nodeuser

WORKDIR /app

# Install dependencies (separate layer — cached unless package.json changes)
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy source
COPY --chown=nodeuser:nodegroup . .

USER nodeuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "src/index.js"]
```

### Static Analysis / CLI Tool

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
```

---

## Multi-Stage Builds

### Build Stage + Minimal Runtime

```dockerfile
# syntax=docker/dockerfile:1

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11 AS builder

WORKDIR /build

# Install build tools
RUN pip install build wheel

COPY pyproject.toml .
COPY src/ src/

# Build wheel
RUN python -m build --wheel --outdir /dist

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --shell /bin/bash appuser

WORKDIR /app

# Only copy the built wheel from builder stage
COPY --from=builder /dist/*.whl .
RUN pip install --no-cache-dir *.whl && rm *.whl

USER appuser

CMD ["my_app"]
```

### Go Application (scratch final image)

```dockerfile
# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM golang:1.22-alpine AS builder

WORKDIR /build

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o app .

# ── Stage 2: Minimal runtime ──────────────────────────────────────────────────
FROM scratch

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /build/app /app

EXPOSE 8080

ENTRYPOINT ["/app"]
```

### Frontend Build + Nginx Serve

```dockerfile
# ── Stage 1: Build frontend ───────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── Stage 2: Serve with Nginx ─────────────────────────────────────────────────
FROM nginx:alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Docker Compose

### Standard Web + Database Stack

```yaml
# docker-compose.yml
version: "3.9"

services:

  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime        # use specific multi-stage target
    image: myapp:latest
    container_name: myapp
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/mydb
      - SECRET_KEY=${SECRET_KEY}     # from .env file
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - ./data:/app/data:ro          # read-only mount
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16-alpine
    container_name: myapp-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - backend

volumes:
  postgres_data:
    driver: local

networks:
  backend:
    driver: bridge
```

### Override File for Development

```yaml
# docker-compose.override.yml (auto-loaded with docker compose up)
version: "3.9"

services:
  app:
    build:
      target: development
    volumes:
      - .:/app                       # live code reload
    environment:
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    command: ["python", "-m", "uvicorn", "app.main:app",
              "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## .dockerignore

```dockerignore
# Version control
.git
.gitignore
.gitattributes

# Documentation
README.md
CHANGELOG.md
docs/
*.md

# Development
.env
.env.*
!.env.example
*.local

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.eggs/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
npm-debug.log*

# Docker
Dockerfile*
docker-compose*

# CI/CD
.github/
.gitlab-ci.yml
Jenkinsfile
.circleci/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets (never include)
*.pem
*.key
*.crt
secrets/
```

---

## Build & Run

```bash
# Build
docker build -t myapp:latest .
docker build -t myapp:1.2.0 .
docker build --target runtime -t myapp:latest .          # specific stage
docker build --no-cache -t myapp:latest .                # force full rebuild
docker build --build-arg ENV=production -t myapp:prod .  # build args

# Run
docker run myapp:latest
docker run -p 8000:8000 myapp:latest
docker run -d --name myapp -p 8000:8000 myapp:latest     # detached
docker run --rm myapp:latest                             # remove on exit
docker run -e SECRET_KEY=abc123 myapp:latest             # env var
docker run -v $(pwd)/data:/app/data myapp:latest         # volume mount
docker run --env-file .env myapp:latest                  # env file

# Docker Compose
docker compose up -d                  # start all services detached
docker compose up --build             # rebuild and start
docker compose down                   # stop and remove containers
docker compose down -v                # also remove volumes
docker compose logs -f app            # follow logs
docker compose exec app bash          # shell into running container
docker compose ps                     # list running services

# Inspect
docker inspect myapp
docker logs myapp -f
docker stats myapp
docker exec -it myapp sh              # interactive shell
```

---

## Security Hardening

```dockerfile
# 1. Always use specific version tags (never 'latest' in production)
FROM python:3.11.9-slim    # not: FROM python:latest

# 2. Non-root user (always)
RUN useradd --uid 1001 --create-home appuser
USER appuser

# 3. Read-only filesystem
# In docker-compose.yml:
#   read_only: true
#   tmpfs:
#     - /tmp

# 4. No new privileges
# In docker-compose.yml:
#   security_opt:
#     - no-new-privileges:true

# 5. Drop capabilities
# In docker-compose.yml:
#   cap_drop:
#     - ALL
#   cap_add:
#     - NET_BIND_SERVICE   # only if needed

# 6. Minimal base image
FROM python:3.11-slim      # not: python:3.11 (full Debian)
# Or even:
FROM gcr.io/distroless/python3-debian12

# 7. Never bake secrets into image
# WRONG: ENV SECRET_KEY=abc123
# RIGHT: Pass at runtime via --env-file or secrets manager

# 8. Pin all apt packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.88.1-10+deb12u5 \
    && rm -rf /var/lib/apt/lists/*
```

---

## Validation & QA

```bash
# Install hadolint (Dockerfile linter)
docker pull hadolint/hadolint
# or: brew install hadolint

# Lint Dockerfile
hadolint Dockerfile
docker run --rm -i hadolint/hadolint < Dockerfile

# Ignore specific rules
hadolint --ignore DL3008 Dockerfile

# Scan image for vulnerabilities
docker scout cves myapp:latest
# or: trivy image myapp:latest

# Verify build succeeds
docker build -t myapp:test . && echo "BUILD PASSED"

# Smoke test — container starts and exits cleanly
docker run --rm myapp:test python --version
docker run --rm myapp:test python -c "from app import main; print('Import OK')"

# Check image size
docker image inspect myapp:latest --format='{{.Size}}' | \
  awk '{printf "Image size: %.1f MB\n", $1/1024/1024}'

# List layers and sizes
docker history myapp:latest
```

```python
# Automated build + smoke test
import subprocess, sys

def docker_qa(tag: str = "myapp:test"):
    steps = [
        (["hadolint", "Dockerfile"],                   "Lint Dockerfile"),
        (["docker", "build", "-t", tag, "."],          "Build image"),
        (["docker", "run", "--rm", tag, "--version"],  "Smoke test"),
    ]

    for cmd, label in steps:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FAIL: {label}\n{result.stderr}")
            sys.exit(1)
        print(f"PASS: {label}")

docker_qa()
```

### QA Checklist

- [ ] Base image pinned to specific version tag (not `latest`)
- [ ] Non-root user created and switched to (`USER appuser`)
- [ ] `.dockerignore` present and excludes secrets, `.git`, dev files
- [ ] Dependencies installed in a separate layer from application code
- [ ] `--no-cache-dir` used with pip / `npm cache clean` with npm
- [ ] `HEALTHCHECK` defined for long-running services
- [ ] No secrets, passwords, or API keys in Dockerfile or image layers
- [ ] `hadolint` passes with zero errors
- [ ] Multi-stage build used if build tools aren't needed at runtime
- [ ] `docker run --rm` smoke test passes
- [ ] Image size is reasonable (flag if >1GB for non-ML workloads)

### QA Loop

1. Write Dockerfile
2. `hadolint Dockerfile` — fix all linting errors
3. `docker build` — confirm build succeeds
4. Smoke test — run container, check basic functionality
5. `docker history` — review layers, spot unnecessary size
6. Security scan — `docker scout cves` or `trivy`
7. **Do not push to registry until all checks pass**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `Permission denied` in container | Running as root but filesystem owned differently | Set correct `--chown` on COPY; use non-root user |
| Image is unexpectedly large | Build artefacts included | Use multi-stage build; check `.dockerignore` |
| `npm ci` fails | `package-lock.json` missing | Commit `package-lock.json` to repo |
| Container exits immediately | CMD fails silently | Run interactively: `docker run -it myapp bash` |
| Health check always unhealthy | App not listening on expected port/path | Verify health endpoint exists before container starts |
| Secrets in image layers | Secret passed as `ENV` or `ARG` | Use `--secret` mount (BuildKit) or pass at runtime |
| Build cache not working | COPY before dependency install | Always `COPY requirements.txt` before `COPY . .` |

---

## Dependencies

```bash
# Linting
brew install hadolint          # macOS
apt install hadolint           # Linux
docker pull hadolint/hadolint  # Docker-based

# Vulnerability scanning
brew install aquasecurity/trivy/trivy   # Trivy
docker scout cves IMAGE                 # Docker Scout (built-in)

# BuildKit (enable for advanced features)
export DOCKER_BUILDKIT=1
```
