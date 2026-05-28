from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = "kontrol-it-practice-secret-key"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'data' / 'kontrol_it.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    GENERATED_DOCS_FOLDER = str(BASE_DIR / "generated" / "documents")
    GENERATED_REPORTS_FOLDER = str(BASE_DIR / "generated" / "reports")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
