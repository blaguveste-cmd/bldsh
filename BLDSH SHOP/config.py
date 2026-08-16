"""Configuration for BLDSH SHOP.

Loads values from a local .env file (next to this file) and then from the
process environment. Process environment variables take precedence.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def _load_dotenv_file(path: Path) -> None:
    """Minimal .env loader; no third-party dependency required."""
    if not path.is_file():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Support simple quoted values.
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]

            # Do not overwrite a variable already supplied by the OS.
            os.environ.setdefault(key, value)
    except OSError as exc:
        print(f"WARNING: failed to read {path}: {exc}")


_load_dotenv_file(ENV_FILE)


# Tokens and secrets
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN", "")
GETSMS_API_KEY = os.getenv("GETSMS_API_KEY", "")

# Admin and integration settings
ADMIN_ID = int(os.getenv("ADMIN_ID", "8591526093"))
LOLZ_API_URL = os.getenv("LOLZ_API_URL", "https://lolz.guru/api/")
GETSMS_API_URL = os.getenv("GETSMS_API_URL", "https://userapi.getsms.shop")

# Payment / UI defaults
RUB_PAYMENT_DETAILS = os.getenv("RUB_PAYMENT_DETAILS", "+79538373056\nЮMoney\nНаталья Юрьевна В.")
STARS_RATE = float(os.getenv("STARS_RATE", "1.2"))
RELAYER_USERNAME = os.getenv("RELAYER_USERNAME", "@BLDSHRelayer")
RELAYER_SESSION = os.getenv("RELAYER_SESSION", "accounts/relayer.session")

# GetSMS service discovery defaults
GETSMS_SERVICE_COUNTRY = os.getenv("GETSMS_SERVICE_COUNTRY", "2")
GETSMS_SERVICE_QUERY = os.getenv("GETSMS_SERVICE_QUERY", "Telegram")
GETSMS_DEFAULT_OPERATOR = os.getenv("GETSMS_DEFAULT_OPERATOR", "any")
GETSMS_MAX_PRICE = float(os.getenv("GETSMS_MAX_PRICE", "999.0"))

# Refund percent (in percent)
REFUND_PERCENT = int(os.getenv("REFUND_PERCENT", "65"))

# Telethon API
API_ID = int(os.getenv("API_ID", "6"))
API_HASH = os.getenv("API_HASH", "eb06d4abfb49dc3eeb1aeb98ae0f581e")
