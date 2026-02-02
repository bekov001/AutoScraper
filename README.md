# KBTU AutoScraper

Selenium script for automatic attendance marking on KBTU Registration Online portal. Supports multiple users.

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
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Create a `users.json` file with your users:

```json
[
  {
    "username": "student1",
    "password": "password1",
    "telegram_chat_id": "123456789"
  },
  {
    "username": "student2",
    "password": "password2",
    "telegram_chat_id": "987654321"
  }
]
```

Each user will receive Telegram notifications to their own chat ID when attendance is marked.

## Usage

```bash
source venv/bin/activate
python open_kbtu.py
```

The script will:
1. Load all users from `users.json`
2. Launch a separate Chrome browser for each user
3. Log in with their credentials
4. Look for the "Отметиться" (check-in) button every 35 seconds
5. Click it automatically if available and send Telegram notification

## Docker

```bash
docker-compose up -d
```

## Requirements

- Python 3.x
- Google Chrome browser
- ChromeDriver (auto-managed by Selenium)
