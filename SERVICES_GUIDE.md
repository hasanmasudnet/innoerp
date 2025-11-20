# Simple Guide to Running innoERP Services

## Quick Start

1. **Activate your virtual environment** (if not already activated):
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Start all services**:
   ```bash
   python start_services.py
   ```

That's it! All 4 services will start automatically.

## What Services Are Running?

- **API Gateway** (port 8000) - Main entry point
- **Tenant Service** (port 8001) - Manages organizations/tenants
- **Auth Service** (port 8002) - Handles authentication
- **User Service** (port 8003) - Manages users

## Access Services

- **API Documentation**: 
  - http://localhost:8000/docs (API Gateway)
  - http://localhost:8001/docs (Tenant Service)
  - http://localhost:8002/docs (Auth Service)
  - http://localhost:8003/docs (User Service)

## Stopping Services

Press `Ctrl+C` in the terminal where services are running. All services will stop automatically.

## Troubleshooting

### Service won't start?
- Make sure your virtual environment is activated
- Check that `.env` file exists in the project root
- Look at the error messages in the terminal

### Port already in use?
- Stop any other services using ports 8000-8003
- Or change the ports in `start_services.py`

### Need to restart a service?
- Stop all services (Ctrl+C)
- Start again with `python start_services.py`

## Notes

- Services run without auto-reload by default (they keep running)
- Logs appear in real-time in the terminal
- All services share the same virtual environment

