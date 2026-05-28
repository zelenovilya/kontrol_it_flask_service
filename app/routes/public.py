from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.models import User, Role, Client, FeedbackMessage, Article, Service

public_bp = Blueprint("public", __name__)

PUBLIC_PAGES = {
    "about": {
        "title": "О компании",
        "lead": "ООО «Контроль ИТ» выполняет сопровождение пользователей, рабочих мест и ИТ-инфраструктуры организаций.",
        "text": "Компания оказывает услуги технической поддержки, администрирования, настройки рабочих мест и базового контроля информационной безопасности.",
    },
    "tariffs": {
        "title": "Тарифы",
        "lead": "Стоимость работ зависит от вида услуги, срочности обращения и состава выполняемых действий.",
        "text": "В сервисе предусмотрена возможность учета платных услуг и формирования документов по результатам выполнения заявки.",
    },
    "how-to-create-ticket": {
        "title": "Как подать заявку",
        "lead": "Клиент создает заявку через личный кабинет, выбирает услугу, приоритет и прикрепляет файл при необходимости.",
        "text": "После отправки заявка получает статус, передается специалисту и отображается в истории обращений клиента.",
    },
    "advantages": {
        "title": "Преимущества сервиса",
        "lead": "Сервис сокращает время регистрации обращений и повышает прозрачность контроля заявок.",
        "text": "Все действия фиксируются в единой базе данных: статусы, комментарии, файлы, документы и исполнитель.",
    },
    "faq": {
        "title": "Частые вопросы",
        "lead": "Раздел содержит ответы на типовые вопросы клиентов по созданию и отслеживанию заявок.",
        "text": "Если вопрос не решен через базу знаний, клиент может направить обращение через форму обратной связи.",
    },
    "contacts": {
        "title": "Контакты",
        "lead": "Связаться с ООО «Контроль ИТ» можно через форму обратной связи или по контактным данным компании.",
        "text": "Адрес: г. Москва. Электронная почта: info@kontrol-it.local. Телефон: +7 900 000-00-00.",
    },
}


@public_bp.route("/")
def home():
    services = Service.query.filter_by(is_active=True).limit(4).all()
    news = Article.query.filter_by(article_type="news", is_published=True).order_by(Article.created_at.desc()).limit(3).all()
    return render_template("public/home.html", title="Главная", services=services, news=news)


@public_bp.route("/services")
def services():
    services_list = Service.query.filter_by(is_active=True).all()
    return render_template("public/services.html", title="Услуги", services=services_list)


@public_bp.route("/knowledge-base")
def knowledge_base():
    articles = Article.query.filter_by(article_type="knowledge", is_published=True).all()
    return render_template("public/articles.html", title="База знаний", articles=articles)


@public_bp.route("/news")
def news():
    articles = Article.query.filter_by(article_type="news", is_published=True).all()
    return render_template("public/articles.html", title="Новости", articles=articles)


@public_bp.route("/article/<slug>")
def article_detail(slug):
    article = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("public/article_detail.html", title=article.title, article=article)


@public_bp.route("/<page_slug>")
def static_page(page_slug):
    page = PUBLIC_PAGES.get(page_slug)
    if page is None:
        return render_template("shared/404.html", title="Страница не найдена"), 404
    return render_template("public/static_page.html", title=page["title"], page=page)


@public_bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        message = FeedbackMessage(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            subject=request.form.get("subject", "").strip(),
            message=request.form.get("message", "").strip(),
        )
        db.session.add(message)
        db.session.commit()
        flash("Сообщение отправлено. Специалист свяжется с вами после обработки обращения.", "success")
        return redirect(url_for("public.feedback"))
    return render_template("public/feedback.html", title="Обратная связь")


@public_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Вход выполнен успешно.", "success")
            if user.has_role("Администратор"):
                return redirect(url_for("admin.dashboard"))
            if user.has_role("Специалист"):
                return redirect(url_for("specialist.dashboard"))
            return redirect(url_for("client.dashboard"))
        flash("Неверный логин или пароль.", "danger")
    return render_template("auth/login.html", title="Вход")


@public_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        organization_name = request.form.get("organization_name", "").strip()
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Пользователь с таким логином или электронной почтой уже существует.", "danger")
            return redirect(url_for("public.register"))
        role = Role.query.filter_by(name="Клиент").first()
        user = User(username=username, email=email, full_name=full_name, password_hash=generate_password_hash(password, method="pbkdf2:sha256"), role=role)
        db.session.add(user)
        db.session.flush()
        db.session.add(Client(user=user, organization_name=organization_name or "Новая организация", contact_person=full_name))
        db.session.commit()
        flash("Регистрация выполнена. Теперь можно войти в личный кабинет.", "success")
        return redirect(url_for("public.login"))
    return render_template("auth/register.html", title="Регистрация")


@public_bp.route("/logout")
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("public.home"))
