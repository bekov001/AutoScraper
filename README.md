# KBTU AutoScraper

Selenium script for automatic attendance marking on KBTU Registration Online portal.

## Setup

### 1. Create virtual environment

```bash
python3 -m venv venv
```

### 2. Activate virtual environment

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

Create a `.env` file in the project root:

```
KBTU_USERNAME=your_username
KBTU_PASSWORD=your_password
```

## Usage

```bash
source venv/bin/activate
python open_kbtu.py
```

The script will:
1. Open Chrome browser
2. Navigate to https://wsp.kbtu.kz/RegistrationOnline
3. Log in with your credentials
4. Look for the "Отметиться" (check-in) button
5. Click it automatically if available

## Requirements

- Python 3.x
- Google Chrome browser
- ChromeDriver (auto-managed by Selenium)
