import os
import time
import logging
import math
import requests
from typing import Optional

LOG_PATH = os.path.join("/app/logs", "ittai_scrape.log")

def get_logger() -> logging.Logger:
    logger = logging.getLogger("ittai")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    return logger

def sleep_delay(sec: Optional[float] = None):
    delay = sec if sec is not None else float(os.environ.get("SCRAPE_DELAY", "2.0"))
    if delay and delay > 0:
        time.sleep(delay)

def get_html(url: str, logger: logging.Logger, timeout: float = 20.0) -> Optional[str]:
    """Shift-JIS想定。失敗時はNone"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ittai-scraper/1.0; +https://example.invalid)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            logger.warning(f"HTTP {r.status_code} for {url}")
            return None
        # 明示的にShift-JIS優先（metaがshift_jis）
        r.encoding = r.encoding or "shift_jis"
        if r.encoding.lower() in ("windows-31j", "cp932", "shift_jisx0213"):
            r.encoding = "shift_jis"
        return r.text
    except Exception as e:
        logger.exception(f"GET failed for {url}: {e}")
        return None