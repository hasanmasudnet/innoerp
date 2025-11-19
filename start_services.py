#!/usr/bin/env python3
"""
Start all innoERP services
This script starts all 4 services (API Gateway, Tenant, Auth, User)
"""
import subprocess
import sys
import os
import time
import signal
import threading
import argparse
from pathlib import Path
from typing import List

# Global list to track subprocesses
processes: List[subprocess.Popen] = []

def print_output(proc, service_name):
    """Print output from a service process"""
    try:
        for line in iter(proc.stdout.readline, ''):
            if line:
                print(f"[{service_name}] {line.rstrip()}")
    except:
        pass

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop all services"""
    print("\n\nStopping all services...")
    for proc in processes:
        if proc.poll() is None:  # Process is still running
            proc.terminate()
    # Wait for processes to terminate
    for proc in processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("[OK] All services stopped")
    sys.exit(0)

def start_service(name: str, port: int, cwd: Path, venv_python: Path, pythonpath: str, reload: bool = False):
    """Start a single service"""
    print(f"Starting {name} on port {port}...")
    if reload:
        print(f"  [INFO] Auto-reload enabled (will restart on code changes)")
    else:
        print(f"  [INFO] Auto-reload disabled (will keep running)")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath
    
    # Build uvicorn command
    cmd = [
        str(venv_python),
        "-u",  # Unbuffered output
        "-m", "uvicorn",
        "app.main:app",
        "--port", str(port),
        "--host", "0.0.0.0"
    ]
    
    # Add --reload only if requested
    if reload:
        cmd.append("--reload")
    
    # Use unbuffered output for real-time logs
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start thread to print output
    thread = threading.Thread(target=print_output, args=(proc, name), daemon=True)
    thread.start()
    
    processes.append(proc)
    return proc

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Start all innoERP services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_services.py              # Start without auto-reload (keeps running)
  python start_services.py --reload     # Start with auto-reload (restarts on code changes)
  python start_services.py --no-reload  # Explicitly disable auto-reload
        """
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload (services will restart on code changes)'
    )
    parser.add_argument(
        '--no-reload',
        action='store_true',
        dest='no_reload',
        help='Disable auto-reload (services will keep running, default behavior)'
    )
    
    args = parser.parse_args()
    
    # Determine reload setting
    # Default: no reload (keep running)
    # --reload: enable reload
    # --no-reload: explicitly disable reload
    use_reload = args.reload and not args.no_reload
    
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    # Check if venv exists
    if not venv_path.exists():
        print("Error: Virtual environment not found!")
        print("Please run: python setup.py")
        sys.exit(1)
    
    # Get venv Python
    if os.name == 'nt':  # Windows
        venv_python = venv_path / "Scripts" / "python.exe"
    else:  # Linux/Mac
        venv_python = venv_path / "bin" / "python"
    
    if not venv_python.exists():
        print(f"Error: Python not found at {venv_python}")
        print("Please run: python setup.py")
        sys.exit(1)
    
    # Set PYTHONPATH
    pythonpath = str(project_root)
    
    # Check .env file
    if not (project_root / ".env").exists():
        print("Warning: .env file not found!")
        print("Services may not connect to the correct database.")
        time.sleep(2)
    
    print("=" * 60)
    print("Starting innoERP Services")
    print("=" * 60)
    if use_reload:
        print("[MODE] Auto-reload ENABLED (services will restart on code changes)")
    else:
        print("[MODE] Auto-reload DISABLED (services will keep running)")
    print()
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start services
    services = [
        ("API Gateway", 8000, project_root / "services" / "api-gateway"),
        ("Tenant Service", 8001, project_root / "services" / "tenant-service"),
        ("Auth Service", 8002, project_root / "services" / "auth-service"),
        ("User Service", 8003, project_root / "services" / "user-service"),
    ]
    
    for name, port, service_path in services:
        if not service_path.exists():
            print(f"Error: Service directory not found: {service_path}")
            continue
        start_service(name, port, service_path, venv_python, pythonpath, reload=use_reload)
        time.sleep(2)  # Stagger service starts
    
    print()
    print("=" * 60)
    print("[OK] All Services Started")
    print("=" * 60)
    print()
    print("Services running:")
    print("  - API Gateway:    http://localhost:8000")
    print("  - Tenant Service: http://localhost:8001")
    print("  - Auth Service:   http://localhost:8002")
    print("  - User Service:   http://localhost:8003")
    print()
    print("API Documentation:")
    print("  - API Gateway:    http://localhost:8000/docs")
    print("  - Tenant Service: http://localhost:8001/docs")
    print("  - Auth Service:   http://localhost:8002/docs")
    print("  - User Service:   http://localhost:8003/docs")
    print()
    print("Press Ctrl+C to stop all services")
    print()
    
    # Wait a bit for services to start
    print("\nWaiting 10 seconds for services to initialize...")
    time.sleep(100)
    
    # Check if services are running
    print("\nChecking service status...")
    all_running = True
    for i, (name, port, _) in enumerate(services):
        if processes[i].poll() is not None:  # Process has terminated
            print(f"[FAIL] {name} has stopped!")
            all_running = False
        else:
            print(f"[OK] {name} is running on port {port}")
    
    if not all_running:
        print("\n[ERROR] Some services failed to start!")
        print("Check the logs above for errors.")
        signal_handler(None, None)
        return
    
    print("\n" + "=" * 60)
    print("[OK] All services are running!")
    print("=" * 60)
    print("\nMonitoring services... (Press Ctrl+C to stop)")
    print("Service logs will appear above.\n")
    
    # Monitor processes
    try:
        while True:
            # Check if any service has stopped
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    print(f"\n[ERROR] {services[i][0]} has stopped unexpectedly!")
            
            # If all stopped, exit
            if all(proc.poll() is not None for proc in processes):
                print("\n[ERROR] All services have stopped!")
                break
            
            time.sleep(50)  # Check every 5 seconds
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

