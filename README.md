# Chess Tournament Manager

Desktop application (Python + `customtkinter`) to manage chess tournaments, players, rounds, matches, and HTML exports.

## Prerequisites

- Python 3.10 or newer
- `pip`

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the program

From the repository root:

```powershell
python main.py
```

The application stores data in:
- `data/players`
- `data/tournaments`

Generated tournament reports are written to:
- `exports/`

## Run tests

```powershell
python -m pytest
```

## Generate a new flake8 HTML report

```powershell
python -m flake8 . --format=html --htmldir=flake-report
```

Open:
- `flake-report/index.html`
