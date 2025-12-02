# FinShare Architecture

## Overview

FinShare is a bill-splitting app built with a microservices architecture. It's designed to be self-hosted and uses **only free, open-source tools** - no paid AI or cloud APIs required.

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  React Web  │  │  iOS App    │  │ Android App │         │
│  │  (TypeScript)│  │  (React    │  │  (React     │         │
│  │             │  │   Native)   │  │   Native)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Kong)                        │
│              Routes requests to services                     │
│                    Port: 8000                                │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Auth Service │  │ Expense Svc  │  │  OCR Service │
│  (Node.js)   │  │  (Node.js)   │  │  (Python +   │
│  Port: 3001  │  │  Port: 3004  │  │  Tesseract)  │
└──────────────┘  └──────────────┘  │  Port: 8001  │
        │                  │        └──────────────┘
        │                  │               │
        ▼                  ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │   MongoDB   │  │    Redis    │         │
│  │  (Main DB)  │  │   (Chat)    │  │   (Cache)   │         │
│  │  Port: 5432 │  │ Port: 27017 │  │ Port: 6379  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  ┌─────────────┐                                            │
│  │   MinIO     │  ← S3-compatible storage for receipts     │
│  │ Port: 9000  │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## Services

### Backend Services (Node.js + TypeScript)

| Service | Port | Purpose |
|---------|------|---------|
| auth-service | 3001 | Login, registration, JWT tokens |
| user-service | 3002 | User profiles, friend management |
| group-service | 3003 | Create/manage expense groups |
| expense-service | 3004 | Add/edit expenses, split calculations |
| chat-service | 3005 | Real-time group messaging |
| notification-service | 3006 | Email and push notifications |
| settlement-service | 3007 | Calculate who owes whom |

### OCR Service (Python)

| Component | What It Does |
|-----------|--------------|
| **Tesseract OCR** | Extracts text from receipt images (FREE!) |
| **OpenCV** | Improves image quality before scanning |
| **FastAPI** | Handles HTTP requests |

**No paid services used!** Google Cloud Vision and AWS Textract have been removed.

## Databases

### PostgreSQL (Main Database)

Stores structured data:
- Users
- Groups and memberships
- Expenses and splits
- Settlements
- Receipt metadata

### MongoDB (Chat)

Stores chat messages - good for:
- Flexible message formats
- Fast reads for message history
- Easy to query by group/user

### Redis (Cache)

Used for:
- User sessions
- Rate limiting
- Caching frequently accessed data
- Real-time features (pub/sub)

## Receipt Scanning Flow

```
1. User takes photo of receipt
              │
              ▼
2. Image sent to OCR Service
              │
              ▼
3. Image preprocessing (OpenCV)
   - Convert to grayscale
   - Remove noise
   - Fix rotation/skew
   - Enhance contrast
              │
              ▼
4. Text extraction (Tesseract - FREE)
              │
              ▼
5. Parse text for:
   - Store name
   - Date
   - Total amount
   - Tax
   - Line items
              │
              ▼
6. Return structured data
              │
              ▼
7. User reviews & edits if needed
              │
              ▼
8. Create expense with data
```

## Tech Stack Summary

| Layer | Technology | Cost |
|-------|------------|------|
| Frontend | React + TypeScript | Free |
| Backend | Node.js + Express | Free |
| OCR | Python + Tesseract | **Free** |
| Main Database | PostgreSQL | Free |
| Chat Database | MongoDB | Free |
| Cache | Redis | Free |
| File Storage | MinIO | Free |
| API Gateway | Kong | Free |
| Containers | Docker | Free |

## What's NOT Included (Paid Services Removed)

These were in the original SpendShare but have been removed:

- ❌ Google Cloud Vision API
- ❌ AWS Textract
- ❌ AWS S3 (replaced with MinIO)
- ❌ Stripe/PayPal integration
- ❌ Firebase Cloud Messaging
- ❌ Sentry (paid tier)
- ❌ DataDog

## Self-Hosting Requirements

Minimum server specs:
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Docker installed

Works on:
- Your own server
- Raspberry Pi (with patience)
- Any VPS (DigitalOcean, Linode, etc.)
- Local machine for development

## Security Considerations

- JWT tokens for authentication
- Password hashing with bcrypt
- HTTPS in production (use Let's Encrypt - free!)
- Input validation on all endpoints
- Rate limiting on API gateway

## Future Improvements

Things you could add later:
- Mobile apps (React Native)
- More OCR languages
- Better receipt parsing
- Export to CSV
- Multi-currency support
