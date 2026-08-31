# Application-wide logger — one continuous chronological text log covering
# sign-in, document upload/extraction, every LLM call, and every review
# action, plus mirrored to console. Call setup_logging() once, at startup
# (see app/main.py). Every other module gets its own child logger via
# logging.getLogger(f"iso_platform.{__name__}") — same file/console handlers,
# but log lines carry their originating module.

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")

    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log", when="midnight", backupCount=14, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger("iso_platform")
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.propagate = False
