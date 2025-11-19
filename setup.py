#!/usr/bin/env python3
"""
Setup script for innoERP
Creates virtual environment and installs all dependencies
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a shell command"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, check=check)
    return result.returncode == 0

def main():
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    print("=" * 60)
    print("innoERP Setup")
    print("=" * 60)
    
    # Check Python version
    print("\nChecking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"Error: Python 3.11+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    
    # Create virtual environment
    print("\nCreating virtual environment...")
    if venv_path.exists():
        print("[OK] Virtual environment already exists")
    else:
        run_command([sys.executable, "-m", "venv", "venv"], cwd=project_root)
        print("[OK] Virtual environment created")
    
    # Get venv Python
    if os.name == 'nt':  # Windows
        venv_python = venv_path / "Scripts" / "python.exe"
        venv_pip = venv_path / "Scripts" / "pip.exe"
    else:  # Linux/Mac
        venv_python = venv_path / "bin" / "python"
        venv_pip = venv_path / "bin" / "pip"
    
    # Upgrade pip (use python -m pip to avoid self-upgrade issues)
    print("\nUpgrading pip...")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_root, check=False)
    print("[OK] pip upgrade attempted")
    
    # Install shared dependencies
    print("\nInstalling shared dependencies...")
    run_command([str(venv_pip), "install", "-r", "shared/requirements.txt"], cwd=project_root)
    print("[OK] Shared dependencies installed")
    
    # Install service dependencies
    services = [
        "tenant-service",
        "auth-service",
        "user-service",
        "api-gateway"
    ]
    
    print("\nInstalling service dependencies...")
    for service in services:
        print(f"  - {service}...")
        service_path = project_root / "services" / service
        if (service_path / "requirements.txt").exists():
            run_command([str(venv_pip), "install", "-r", "requirements.txt"], cwd=service_path)
        else:
            print(f"    Warning: requirements.txt not found for {service}")
    
    # Install testing dependencies
    print("\nInstalling testing dependencies...")
    run_command([str(venv_pip), "install", "requests"], cwd=project_root)
    print("[OK] Testing dependencies installed")
    
    print("\n" + "=" * 60)
    print("[OK] Setup Complete!")
    print("=" * 60)
    print("\nTo activate virtual environment:")
    if os.name == 'nt':
        print("  .\\venv\\Scripts\\Activate.ps1")
    else:
        print("  source venv/bin/activate")
    print("\nTo start services:")
    print("  python start_services.py")

if __name__ == "__main__":
    main()

