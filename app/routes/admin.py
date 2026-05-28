from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from openpyxl import Workbook
from werkzeug.security import generate_password_hash
from app import db
from app.decorators import role_required
from app.models import (
    User, Role, Client, Employee, Service, ServiceCategory, Ticket,
    TicketStatus, FeedbackMessage, Article
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("Администратор")
def dashboard():
    stats = {
        "users": User.query.count(),
        "clients": Client.query.count(),
        "employees": Employee.query.count(),
        "tickets": Ticket.query.count(),
        "services": Service.query.count(),
        "feedback": FeedbackMessage.query.filter_by(is_processed=False).count(),
    }
    return render_template("admin/dashboard.html", title="Административная панель", stats=stats)


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def users():
    roles = Role.query.all()
    if request.method == "POST":
        user = User(
            username=request.form.get("username", "").strip(),
            email=request.form.get("email", "").strip(),
            full_name=request.form.get("full_name", "").strip(),
            phone=request.form.get("phone", "").strip(),
            password_hash=generate_password_hash(request.form.get("password", "123456"), method="pbkdf2:sha256"),
            role_id=int(request.form.get("role_id")),
        )
        db.session.add(user)
        db.session.commit()
        flash("Пользователь добавлен.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/users.html", title="Пользователи", users=User.query.all(), roles=roles)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    if request.method == "POST":
        user.username = request.form.get("username", "").strip()
        user.email = request.form.get("email", "").strip()
        user.full_name = request.form.get("full_name", "").strip()
        user.phone = request.form.get("phone", "").strip()
        user.role_id = int(request.form.get("role_id"))
        user.is_active_account = request.form.get("is_active_account") == "on"
        password = request.form.get("password", "").strip()
        if password:
            user.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        db.session.commit()
        flash("Данные пользователя обновлены.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_edit.html", title="Редактирование пользователя", user=user, roles=roles)


@admin_bp.route("/users/<int:user_id>/toggle-active")
@login_required
@role_required("Администратор")
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Нельзя заблокировать текущую учетную запись администратора.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash("Статус учетной записи изменен.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/roles", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def roles():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if Role.query.filter_by(name=name).first():
            flash("Роль с таким названием уже существует.", "danger")
            return redirect(url_for("admin.roles"))
        db.session.add(Role(name=name, description=description))
        db.session.commit()
        flash("Роль добавлена.", "success")
        return redirect(url_for("admin.roles"))
    permissions = {
        "Администратор": "Управление пользователями, ролями, справочниками, заявками, материалами, обратной связью и отчетами.",
        "Специалист": "Просмотр новых и назначенных заявок, смена статусов, комментарии, файлы, акты и Excel-отчеты.",
        "Клиент": "Создание заявок, просмотр своих обращений, комментарии, профиль и скачивание документов.",
    }
    return render_template("admin/roles.html", title="Роли и права доступа", roles=Role.query.all(), permissions=permissions)


@admin_bp.route("/clients")
@login_required
@role_required("Администратор")
def clients():
    return render_template("admin/clients.html", title="Клиенты", clients=Client.query.all())


@admin_bp.route("/employees")
@login_required
@role_required("Администратор")
def employees():
    return render_template("admin/employees.html", title="Сотрудники", employees=Employee.query.all())


@admin_bp.route("/services", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def services():
    categories = ServiceCategory.query.all()
    if request.method == "POST":
        service = Service(
            name=request.form.get("name", "").strip(),
            description=request.form.get("description", "").strip(),
            price=float(request.form.get("price") or 0),
            category_id=int(request.form.get("category_id")),
        )
        db.session.add(service)
        db.session.commit()
        flash("Услуга добавлена.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/services.html", title="Услуги", services=Service.query.all(), categories=categories)


@admin_bp.route("/tickets")
@login_required
@role_required("Администратор")
def tickets():
    return render_template("admin/tickets.html", title="Заявки", tickets=Ticket.query.order_by(Ticket.created_at.desc()).all())


@admin_bp.route("/statuses", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def statuses():
    if request.method == "POST":
        status = TicketStatus(name=request.form.get("name", "").strip(), sort_order=int(request.form.get("sort_order") or 0))
        db.session.add(status)
        db.session.commit()
        flash("Статус добавлен.", "success")
        return redirect(url_for("admin.statuses"))
    return render_template("admin/statuses.html", title="Статусы заявок", statuses=TicketStatus.query.order_by(TicketStatus.sort_order).all())


@admin_bp.route("/feedback")
@login_required
@role_required("Администратор")
def feedback():
    messages = FeedbackMessage.query.order_by(FeedbackMessage.created_at.desc()).all()
    return render_template("admin/feedback.html", title="Обратная связь", messages=messages)


@admin_bp.route("/feedback/<int:message_id>/processed")
@login_required
@role_required("Администратор")
def mark_feedback_processed(message_id):
    message = FeedbackMessage.query.get_or_404(message_id)
    message.is_processed = True
    db.session.commit()
    flash("Обращение отмечено как обработанное.", "success")
    return redirect(url_for("admin.feedback"))


@admin_bp.route("/articles", methods=["GET", "POST"])
@login_required
@role_required("Администратор")
def articles():
    if request.method == "POST":
        article = Article(
            title=request.form.get("title", "").strip(),
            slug=request.form.get("slug", "").strip(),
            summary=request.form.get("summary", "").strip(),
            content=request.form.get("content", "").strip(),
            article_type=request.form.get("article_type", "knowledge"),
        )
        db.session.add(article)
        db.session.commit()
        flash("Материал добавлен.", "success")
        return redirect(url_for("admin.articles"))
    return render_template("admin/articles.html", title="Новости и база знаний", articles=Article.query.order_by(Article.created_at.desc()).all())


@admin_bp.route("/reports")
@login_required
@role_required("Администратор")
def reports():
    tickets_by_status = [(status.name, Ticket.query.filter_by(status=status).count()) for status in TicketStatus.query.order_by(TicketStatus.sort_order).all()]
    return render_template("admin/reports.html", title="Отчеты", tickets_by_status=tickets_by_status)


@admin_bp.route("/reports/tickets.xlsx")
@login_required
@role_required("Администратор")
def tickets_report():
    wb = Workbook()
    ws = wb.active
    ws.title = "Заявки"
    ws.append(["№", "Дата", "Клиент", "Услуга", "Статус", "Приоритет", "Исполнитель"])
    for ticket in Ticket.query.order_by(Ticket.created_at.desc()).all():
        ws.append([
            ticket.id,
            ticket.created_at.strftime("%d.%m.%Y %H:%M"),
            ticket.client.organization_name,
            ticket.service.name,
            ticket.status.name,
            ticket.priority.name,
            ticket.specialist.user.full_name if ticket.specialist else "Не назначен",
        ])
    file_path = Path(current_app.config["GENERATED_REPORTS_FOLDER"]) / "admin_tickets_report.xlsx"
    wb.save(file_path)
    return send_file(file_path, as_attachment=True)
