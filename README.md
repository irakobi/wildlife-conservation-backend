# Wildlife Conservation FastAPI Backend

A modern, scalable API for wildlife conservation data collection with Kobo Toolbox integration.

## Features

- 🦁 Wildlife incident reporting and management
- 📋 Kobo Toolbox form integration
- 🗺️ GPS/spatial data support with PostGIS
- 👥 User authentication and authorization
- 📊 Real-time analytics and reporting
- 🔄 Bi-directional data synchronization
- 📱 Mobile-friendly API design

## Quick Start

1. **Set up Neon Database**: https://neon.tech/
2. **Get Kobo API Token**: Settings → Security in Kobo Toolbox
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Configure Environment**: Copy `.env.example` to `.env` and update values
5. **Run Server**: `python run_server.py`
6. **Test API**: `python test_backend.py`

## API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
wildlife-conservation-backend/
├── app/                 # Main application code
├── tests/              # Test files
├── scripts/            # Setup and utility scripts
├── docs/               # Documentation
└── uploads/            # File uploads directory
```

## Support

For questions or issues, check the documentation in the `docs/` folder.
