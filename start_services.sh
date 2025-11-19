#!/bin/bash

# Start innoERP services for testing

echo "Starting innoERP services..."

# Start infrastructure
echo "Starting infrastructure services..."
cd infrastructure
docker-compose up -d postgres kafka zookeeper

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
cd ..
python infrastructure/init_db.py

# Start services in background
echo "Starting microservices..."

# API Gateway
cd services/api-gateway
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_GATEWAY_PID=$!
cd ../..

# Tenant Service
cd services/tenant-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
TENANT_SERVICE_PID=$!
cd ../..

# Auth Service
cd services/auth-service
uvicorn app.main:app --host 0.0.0.0 --port 8002 &
AUTH_SERVICE_PID=$!
cd ../..

# User Service
cd services/user-service
uvicorn app.main:app --host 0.0.0.0 --port 8003 &
USER_SERVICE_PID=$!
cd ../..

echo "Services started!"
echo "API Gateway: http://localhost:8000"
echo "Tenant Service: http://localhost:8001"
echo "Auth Service: http://localhost:8002"
echo "User Service: http://localhost:8003"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $API_GATEWAY_PID $TENANT_SERVICE_PID $AUTH_SERVICE_PID $USER_SERVICE_PID" EXIT
wait

