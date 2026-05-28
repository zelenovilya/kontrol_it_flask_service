from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename


def save_uploaded_file(file_storage, upload_folder, prefix="file"):
    if not file_storage or not file_storage.filename:
        return None
    original_name = file_storage.filename
    safe_name = secure_filename(original_name)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{prefix}_{timestamp}_{safe_name}"
    target_path = Path(upload_folder) / stored_name
    file_storage.save(target_path)
    return original_name, stored_name, str(target_path)
