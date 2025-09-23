# Setup Guide

## Prerequisites

1. Python 3.9+
2. Neon PostgreSQL account (free at https://neon.tech)
3. Kobo Toolbox account with API token

## Installation Steps

1. **Clone/Download Project**
2. **Create Virtual Environment**: `python -m venv venv`
3. **Activate Environment**: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. **Install Dependencies**: `pip install -r requirements.txt`
5. **Configure Environment**: Copy `.env.example` to `.env` and update values
6. **Run Server**: `python run_server.py`
7. **Test API**: Visit http://localhost:8000/docs

## Configuration

### Neon Database Setup
1. Create account at https://neon.tech
2. Create new project: "wildlife-conservation"
3. Copy connection string to DATABASE_URL in .env
4. Run: `python scripts/setup_database.py`

### Kobo API Setup
1. Login to your Kobo account
2. Go to Settings → Security
3. Copy API Token to KOBO_API_TOKEN in .env

## Verification

Run the test suite: `python test_backend.py`

All endpoints should return successful responses.
