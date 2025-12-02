# FinShare

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> A free, open-source bill splitting app - no paid AI services required

FinShare helps friends, families, and roommates split expenses easily. It includes free receipt scanning powered by Tesseract OCR (runs locally, no API costs).

## Features

- **Smart Expense Splitting** - Split equally, by percentage, or custom amounts
- **Group Management** - Create groups for trips, households, or friend circles
- **Free Receipt Scanning** - Snap a photo, auto-extract amounts (Tesseract OCR)
- **Group Chat** - Discuss expenses with your group
- **Balance Tracking** - See who owes whom at a glance
- **Self-Hosted** - Your data stays on your servers

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/FinShare.git
cd FinShare

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the app
open http://localhost:3000
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript |
| Backend | Node.js + Express |
| OCR | Python + Tesseract (FREE) |
| Databases | PostgreSQL, MongoDB, Redis |
| Storage | MinIO (S3-compatible) |
| Containers | Docker + Docker Compose |

## No Paid AI Services

This project intentionally avoids paid AI/ML services:

- ✅ **Tesseract OCR** - Free, open-source, runs locally
- ❌ ~~Google Cloud Vision~~ - Removed (paid)
- ❌ ~~AWS Textract~~ - Removed (paid)
- ❌ ~~OpenAI APIs~~ - Not used

## Project Structure

```
FinShare/
├── backend/                 # Node.js microservices
│   ├── auth-service/       # Login, registration, JWT
│   ├── user-service/       # User profiles, friends
│   ├── group-service/      # Group management
│   ├── expense-service/    # Expense CRUD, splitting
│   ├── chat-service/       # Real-time messaging
│   ├── notification-service/
│   ├── settlement-service/ # Balance calculations
│   └── shared/             # Shared utilities
├── ocr-service/            # Python + Tesseract
├── frontend/
│   ├── web/               # React web app
│   └── mobile/            # React Native (future)
├── infrastructure/
│   └── docker/            # Docker configs
└── docs/                  # Documentation
```

## Documentation

- [Quick Start Guide](./QUICKSTART.md)
- [Full Setup Guide](./SETUP.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Contributing Guide](./CONTRIBUTING.md)

## License

MIT License - see [LICENSE](./LICENSE)

---

Built with ❤️ - No expensive AI APIs required!
