from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, abort
from flask_login import login_required, current_user
from app import db
from app.decorators import role_required
from app.models import Service, Ticket, TicketStatus, TicketPriority, TicketComment, Attachment, Document
from app.utils import save_uploaded_file

client_bp = Blueprint("client", __name__, url_prefix="/client")


def client_breadcrumbs(*items):
    trail = [{"label": "Главная", "url": url_for("public.home")}]
    if items:
        trail.append({"label": "Личный кабинет клиента", "url": url_for("client.dashboard")})
        trail.extend(items)
    else:
        trail.append({"label": "Личный кабинет клиента", "url": None})
    return trail


@client_bp.route("/dashboard")
@login_required
@role_required("Клиент")
def dashboard():
    client = current_user.client
    tickets = Ticket.query.filter_by(client=client).order_by(Ticket.created_at.desc()).all()
    return render_template(
        "client/dashboard.html",
        title="Панель клиента",
        tickets=tickets,
        breadcrumbs=client_breadcrumbs(),
    )


@client_bp.route("/tickets")
@login_required
@role_required("Клиент")
def tickets():
    tickets_list = Ticket.query.filter_by(client=current_user.client).order_by(Ticket.created_at.desc()).all()
    return render_template(
        "client/tickets.html",
        title="Мои заявки",
        tickets=tickets_list,
        breadcrumbs=client_breadcrumbs({"label": "Мои заявки", "url": None}),
    )


@client_bp.route("/tickets/create", methods=["GET", "POST"])
@login_required
@role_required("Клиент")
def create_ticket():
    services = Service.query.filter_by(is_active=True).all()
    priorities = TicketPriority.query.all()
    if request.method == "POST":
        status = TicketStatus.query.order_by(TicketStatus.sort_order).first()
        ticket = Ticket(
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            service_id=int(request.form.get("service_id")),
            priority_id=int(request.form.get("priority_id")),
            status=status,
            client=current_user.client,
        )
        db.session.add(ticket)
        db.session.flush()
        uploaded = save_uploaded_file(request.files.get("file"), current_app.config["UPLOAD_FOLDER"], prefix=f"ticket_{ticket.id}")
        if uploaded:
            original_name, stored_name, file_path = uploaded
            db.session.add(Attachment(original_name=original_name, stored_name=stored_name, file_path=file_path, ticket=ticket, uploaded_by_id=current_user.id))
        db.session.add(TicketComment(ticket=ticket, author_id=current_user.id, text="Заявка создана клиентом."))
        db.session.commit()
        flash("Заявка создана и передана в обработку.", "success")
        return redirect(url_for("client.ticket_detail", ticket_id=ticket.id))
    return render_template(
        "client/create_ticket.html",
        title="Создать заявку",
        services=services,
        priorities=priorities,
        breadcrumbs=client_breadcrumbs({"label": "Создание заявки", "url": None}),
    )


@client_bp.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
@login_required
@role_required("Клиент")
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.client_id != current_user.client.id:
        abort(403)
    if request.method == "POST":
        text = request.form.get("comment", "").strip()
        if text:
            db.session.add(TicketComment(ticket=ticket, author_id=current_user.id, text=text))
            db.session.commit()
            flash("Комментарий добавлен.", "success")
        return redirect(url_for("client.ticket_detail", ticket_id=ticket.id))
    return render_template(
        "client/ticket_detail.html",
        title=f"Заявка №{ticket.id}",
        ticket=ticket,
        breadcrumbs=client_breadcrumbs(
            {"label": "Мои заявки", "url": url_for("client.tickets")},
            {"label": f"Заявка №{ticket.id}", "url": None},
        ),
    )


@client_bp.route("/documents")
@login_required
@role_required("Клиент")
def documents():
    docs = Document.query.join(Ticket).filter(Ticket.client_id == current_user.client.id).order_by(Document.created_at.desc()).all()
    return render_template(
        "client/documents.html",
        title="Документы",
        documents=docs,
        breadcrumbs=client_breadcrumbs({"label": "Документы", "url": None}),
    )


@client_bp.route("/documents/<int:document_id>/download")
@login_required
@role_required("Клиент")
def download_document(document_id):
    doc = Document.query.get_or_404(document_id)
    if doc.ticket.client_id != current_user.client.id:
        abort(403)
    return send_file(doc.file_path, as_attachment=True)


@client_bp.route("/profile")
@login_required
@role_required("Клиент")
def profile():
    return render_template(
        "client/profile.html",
        title="Профиль клиента",
        client=current_user.client,
        breadcrumbs=client_breadcrumbs({"label": "Профиль", "url": None}),
    )


@client_bp.route("/help")
@login_required
@role_required("Клиент")
def help_page():
    return render_template(
        "client/help.html",
        title="Справка клиента",
        breadcrumbs=client_breadcrumbs({"label": "Справка клиента", "url": None}),
    )
