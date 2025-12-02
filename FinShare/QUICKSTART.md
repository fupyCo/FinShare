# FinShare Quick Start

Get FinShare running in under 5 minutes!

## Prerequisites

- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop)
- **Git** - [Download here](https://git-scm.com/downloads)

That's it! Docker handles everything else.

## Step 1: Clone & Configure

```bash
# Clone the repo
git clone https://github.com/yourusername/FinShare.git
cd FinShare

# Copy environment file (defaults work for local dev)
cp .env.example .env
```

## Step 2: Start Services

```bash
# Start everything
docker-compose up -d

# Wait ~30 seconds for services to start
docker-compose ps
```

## Step 3: Access the App

| Service | URL | Description |
|---------|-----|-------------|
| **API Gateway** | http://localhost:8000 | Main API endpoint |
| **OCR Service** | http://localhost:8001 | Receipt scanning |
| **MailHog** | http://localhost:8025 | Email testing UI |
| **MinIO Console** | http://localhost:9001 | File storage UI |

MinIO login: `minioadmin` / `minioadmin`

## Step 4: Test Receipt Scanning

```bash
# Check OCR service is healthy
curl http://localhost:8001/health

# Scan a receipt (replace with your image path)
curl -X POST "http://localhost:8001/scan" \
  -F "file=@/path/to/your/receipt.jpg"
```

## Stopping Services

```bash
# Stop everything
docker-compose down

# Stop and delete all data
docker-compose down -v
```

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 5432 (for example)
lsof -i :5432

# Kill it
kill -9 <PID>
```

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs ocr-service
```

### Reset Everything
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d
```

## What's Running

After `docker-compose up -d`, you have:

- **PostgreSQL** (port 5432) - Main database
- **MongoDB** (port 27017) - Chat messages
- **Redis** (port 6379) - Cache
- **MinIO** (ports 9000, 9001) - File storage
- **MailHog** (ports 1025, 8025) - Email testing
- **OCR Service** (port 8001) - Receipt scanning
- **API Gateway** (port 8000) - Routes API calls

## Next Steps

1. Check out [SETUP.md](./SETUP.md) for full development setup
2. Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system
3. Look at [CONTRIBUTING.md](./CONTRIBUTING.md) to add features

---

**No paid AI services required!** 🎉
