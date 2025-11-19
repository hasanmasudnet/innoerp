# Setup Instructions

## Virtual Environment Location

**Install virtual environment in the project root: `innoERP/`**

```
innoERP/
├── venv/              ← Virtual environment created here
├── setup.py           ← Run this script
├── start_services.py
├── services/
├── shared/
└── infrastructure/
```

## Steps

### 1. Navigate to Project Root

```bash
cd /path/to/innoERP
```

### 2. Run Setup Script

```bash
python3 setup.py
```

This will:

- Create `venv/` directory in `innoERP/`
- Install FastAPI, uvicorn, SQLAlchemy, and all dependencies inside `venv/`
- Install all service dependencies

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

After activation, you'll see `(venv)` in your terminal prompt.

### 4. Verify Installation

```bash
python -c "import fastapi; print(fastapi.__version__)"
```

Should print the FastAPI version.

## Important Notes

- **venv location**: `innoERP/venv/` (project root)
- **FastAPI installed in**: `innoERP/venv/lib/python3.x/site-packages/`
- **Always activate venv** before running services or scripts
- **PYTHONPATH** should be set to project root: `export PYTHONPATH=$(pwd)`
