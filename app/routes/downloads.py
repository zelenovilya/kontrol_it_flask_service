from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, send_from_directory, url_for
from flask_login import current_user, login_required

from app.models import Attachment, Document

downloads_bp = Blueprint("downloads", __name__, url_prefix="/download")


def can_access_ticket(ticket):
    if current_user.has_role("Администратор"):
        return True
    if current_user.has_role("Клиент") and current_user.client:
        return ticket.client_id == current_user.client.id
    if current_user.has_role("Специалист") and current_user.employee:
        return ticket.specialist_id == current_user.employee.id
    return False


def ticket_redirect_url(ticket):
    if current_user.has_role("Администратор"):
        return url_for("admin.ticket_detail", ticket_id=ticket.id)
    if current_user.has_role("Специалист"):
        return url_for("specialist.ticket_detail", ticket_id=ticket.id)
    if current_user.has_role("Клиент"):
        return url_for("client.ticket_detail", ticket_id=ticket.id)
    return url_for("public.home")


def safe_resolve(file_path, allowed_folder):
    allowed_root = Path(allowed_folder).resolve()
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = allowed_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(allowed_root)
    except ValueError:
        abort(404)
    return resolved


@downloads_bp.route("/attachments/<int:attachment_id>")
@login_required
def attachment(attachment_id):
    item = Attachment.query.get_or_404(attachment_id)
    if not can_access_ticket(item.ticket):
        abort(403)

    file_path = safe_resolve(item.file_path, current_app.config["UPLOAD_FOLDER"])
    if not file_path.is_file():
        flash(f"Файл «{item.original_name}» отсутствует на диске. Запись о вложении сохранена в заявке.", "warning")
        return redirect(ticket_redirect_url(item.ticket))

    return send_from_directory(
        file_path.parent,
        file_path.name,
        as_attachment=True,
        download_name=item.original_name,
    )


@downloads_bp.route("/documents/<int:document_id>")
@login_required
def document(document_id):
    item = Document.query.get_or_404(document_id)
    if not can_access_ticket(item.ticket):
        abort(403)

    file_path = safe_resolve(item.file_path, current_app.config["GENERATED_DOCS_FOLDER"])
    if not file_path.is_file():
        flash(f"Документ «{item.title}» отсутствует на диске. Его можно сформировать повторно.", "warning")
        return redirect(ticket_redirect_url(item.ticket))

    return send_from_directory(
        file_path.parent,
        file_path.name,
        as_attachment=True,
        download_name=file_path.name,
    )
