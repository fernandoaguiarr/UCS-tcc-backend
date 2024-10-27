import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

SUPPORTED_TYPE_FILES = [
    "csv",
    "json",
    "xlsx",
    "xls",
    "xml",
    "zip"
]

SUPPORTED_MIME_TYPE_FILES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/json",
    "text/csv",
    "text/plain",
    "application/xml",
    "application/zip"
]
