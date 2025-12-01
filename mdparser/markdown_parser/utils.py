# markdown_parser/utils.py
import hashlib
from typing import Any

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()