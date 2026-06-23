from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models import Article, Client, FeedbackMessage, Role, Service, User

public_bp = Blueprint("public", __name__)


PUBLIC_PAGES = {
    "about": {
        "title": "О компании",
        "lead": "ООО «Контроль ИТ» сопровождает рабочие места, пользователей и инфраструктуру организаций.",
        "intro": (
            "Компания помогает клиентам фиксировать ИТ-инциденты, контролировать сроки реакции, "
            "видеть историю работ и получать документы по результатам обслуживания."
        ),
        "sections": [
            {
                "title": "Чем занимается компания",
                "text": (
                    "Команда принимает заявки на удаленную диагностику, настройку рабочих мест, "
                    "поддержку сетевых ресурсов, учетных записей, резервного копирования и базовой защиты."
                ),
                "items": [
                    "поддержка пользователей и офисной техники;",
                    "сопровождение серверов и локальной сети;",
                    "учет статусов, комментариев и приложенных файлов;",
                    "формирование актов и отчетов по выполненным работам.",
                ],
            },
            {
                "title": "Как устроена работа",
                "text": (
                    "Каждая заявка проходит единый маршрут: регистрация клиентом, назначение специалиста, "
                    "уточнение деталей, выполнение работ и закрытие с документальным подтверждением."
                ),
                "items": [
                    "клиент видит только свои обращения;",
                    "специалист работает с назначенными заявками;",
                    "администратор управляет справочниками, пользователями и отчетами.",
                ],
            },
        ],
        "cards": [
            {"title": "Прозрачность", "text": "Статусы, комментарии и файлы сохраняются в карточке заявки."},
            {"title": "Контроль сроков", "text": "Приоритет заявки задает ожидаемое время реакции специалиста."},
            {"title": "Единая база", "text": "Данные клиентов, услуг, заявок и документов хранятся в SQLite."},
        ],
    },
    "tariffs": {
        "title": "Тарифы",
        "lead": "Стоимость обслуживания зависит от вида услуги, приоритета заявки и объема работ.",
        "intro": (
            "В учебном сервисе тарифы представлены как справочная публичная страница. "
            "Фактическая стоимость услуги выбирается в карточке заявки из справочника услуг."
        ),
        "sections": [
            {
                "title": "Базовое сопровождение",
                "text": "Подходит для плановых обращений, настройки рабочих мест и консультаций пользователей.",
                "items": [
                    "регистрация заявки через личный кабинет;",
                    "ответ специалиста в рамках выбранного приоритета;",
                    "комментарии и история обработки в карточке заявки.",
                ],
            },
            {
                "title": "Расширенное обслуживание",
                "text": "Используется для серверов, сетевых ресурсов и работ с повышенными требованиями к срокам.",
                "items": [
                    "назначение ответственного специалиста;",
                    "загрузка диагностических файлов и скриншотов;",
                    "формирование акта выполненных работ в формате DOCX.",
                ],
            },
        ],
        "table": {
            "headers": ["Пакет", "Для каких заявок", "Контроль результата"],
            "rows": [
                ["Старт", "Единичные обращения пользователей", "Комментарии и смена статуса"],
                ["Офис", "Рабочие места, принтеры, почта, доступы", "Файлы, исполнитель, акт"],
                ["Инфраструктура", "Серверы, сеть, резервное копирование", "Отчет Excel и документы"],
            ],
        },
    },
    "how-to-create-ticket": {
        "title": "Как подать заявку",
        "lead": "Заявка создается из личного кабинета клиента и сразу попадает в единую очередь обработки.",
        "intro": (
            "Для корректной обработки обращения важно выбрать услугу, указать приоритет, подробно описать проблему "
            "и приложить файл, если специалисту понадобится скриншот или диагностический документ."
        ),
        "steps": [
            "Зарегистрируйтесь или войдите под учетной записью клиента.",
            "Откройте раздел «Мои заявки» и нажмите кнопку создания новой заявки.",
            "Выберите услугу и приоритет, заполните тему и описание проблемы.",
            "При необходимости прикрепите файл с ошибкой, актом или дополнительными данными.",
            "Отправьте заявку и отслеживайте комментарии, статус и документы в карточке обращения.",
        ],
        "sections": [
            {
                "title": "Что указать в описании",
                "text": "Чем точнее описание, тем быстрее специалист сможет воспроизвести проблему и предложить решение.",
                "items": [
                    "когда появилась ошибка;",
                    "на каком рабочем месте или сервисе она возникает;",
                    "какие действия уже выполнялись;",
                    "нужен ли срочный ответ или можно выполнить работу планово.",
                ],
            },
            {
                "title": "После отправки",
                "text": (
                    "Заявка получает начальный статус, появляется в кабинете администратора и может быть назначена "
                    "специалисту. Клиент видит обновления без обращения по телефону."
                ),
                "items": [
                    "смена статуса отображается в карточке;",
                    "новые комментарии сохраняются в истории;",
                    "сформированные документы доступны для скачивания.",
                ],
            },
        ],
    },
    "advantages": {
        "title": "Преимущества сервиса",
        "lead": "Система делает поддержку клиентов управляемой: обращения не теряются, а результат фиксируется документально.",
        "intro": (
            "Веб-сервис объединяет публичные страницы, личные кабинеты, административную панель, "
            "учет заявок, файлов и документов в одном Flask-приложении."
        ),
        "cards": [
            {"title": "Единая карточка заявки", "text": "В ней собраны услуга, клиент, исполнитель, статус, комментарии и файлы."},
            {"title": "Разделение ролей", "text": "Клиент, специалист и администратор видят только нужные им функции."},
            {"title": "Документы", "text": "Специалист формирует акт DOCX, администратор и специалист выгружают отчеты XLSX."},
            {"title": "Проверяемость", "text": "SQLite-база с тестовыми данными позволяет быстро показать работу проекта."},
        ],
        "sections": [
            {
                "title": "Для клиента",
                "text": "Клиенту не нужно уточнять статус обращения по телефону: ход работ виден в личном кабинете.",
                "items": ["создание заявки;", "прикрепление файла;", "комментарии;", "скачивание документов."],
            },
            {
                "title": "Для специалиста",
                "text": "Исполнитель получает список назначенных работ, меняет статус и фиксирует результат.",
                "items": ["очередь заявок;", "история работ;", "акт выполненных работ;", "отчет по выполненным заявкам."],
            },
            {
                "title": "Для администратора",
                "text": "Администратор управляет пользователями, справочниками, заявками, материалами и отчетами.",
                "items": ["статистика;", "назначение специалистов;", "публичные материалы;", "обратная связь."],
            },
        ],
    },
    "faq": {
        "title": "Частые вопросы",
        "lead": "Ответы на типовые вопросы о регистрации, заявках, файлах и документах.",
        "intro": (
            "Раздел помогает клиентам быстрее разобраться с порядком работы сервиса и понять, "
            "какие действия доступны в личном кабинете."
        ),
        "faq": [
            {
                "question": "Можно ли создать заявку без регистрации?",
                "answer": "Нет. Регистрация нужна, чтобы связать обращение с организацией и ограничить доступ к данным.",
            },
            {
                "question": "Кто видит приложенные файлы?",
                "answer": "Клиент видит файлы своих заявок, специалист видит файлы назначенных заявок, администратор видит все файлы.",
            },
            {
                "question": "Где скачать акт выполненных работ?",
                "answer": "После формирования акта специалистом документ появляется в карточке заявки и разделе документов клиента.",
            },
            {
                "question": "Что делать, если нужно уточнить проблему?",
                "answer": "Добавьте комментарий в карточке заявки. История переписки сохраняется вместе со статусами.",
            },
        ],
        "sections": [
            {
                "title": "Если ответа нет в списке",
                "text": "Отправьте сообщение через форму обратной связи. Администратор увидит его в закрытой панели.",
                "items": ["укажите тему обращения;", "оставьте email и телефон;", "опишите вопрос без лишних персональных данных."],
            },
        ],
    },
    "contacts": {
        "title": "Контакты",
        "lead": "Связаться с ООО «Контроль ИТ» можно через форму обратной связи или по учебным контактным данным.",
        "intro": (
            "Страница показывает, как публичная часть сервиса помогает клиенту найти канал связи "
            "и перейти к регистрации обращения."
        ),
        "sections": [
            {
                "title": "Контактные данные",
                "text": "Адрес: г. Москва, учебный офис ООО «Контроль ИТ». Email: info@kontrol-it.local. Телефон: +7 900 000-00-00.",
                "items": [
                    "по вопросам обслуживания используйте личный кабинет;",
                    "по общим вопросам отправьте форму обратной связи;",
                    "по срочным инцидентам создайте заявку с высоким приоритетом.",
                ],
            },
            {
                "title": "Что написать в обращении",
                "text": "Кратко укажите организацию, контактное лицо, тему вопроса и удобный способ связи.",
                "items": ["ФИО или название организации;", "email и телефон;", "тема обращения;", "подробное описание ситуации."],
            },
        ],
        "cards": [
            {"title": "Обратная связь", "text": "Публичная форма сохраняет сообщение в базе данных для администратора."},
            {"title": "Личный кабинет", "text": "Для технических работ лучше создать заявку после входа в систему."},
        ],
    },
    "help": {
        "title": "Справка по системе",
        "lead": "Краткое руководство по ролям, заявкам, файлам, документам и отчетам веб-сервиса.",
        "intro": (
            "Сервис разработан как учебный сетевой ресурс на Flask для учета и обработки заявок клиентов "
            "на ИТ-обслуживание ООО «Контроль ИТ». Автор работы: Зеленов Илья Денисович."
        ),
        "sections": [
            {
                "title": "Роли пользователей",
                "text": "В системе используются три основные роли: клиент, специалист и администратор.",
                "items": [
                    "клиент создает заявки, добавляет комментарии и скачивает документы;",
                    "специалист обрабатывает назначенные заявки и формирует акты;",
                    "администратор управляет пользователями, справочниками, заявками и отчетами.",
                ],
            },
            {
                "title": "Работа с заявками",
                "text": "Заявка проходит путь от создания до закрытия, а все изменения сохраняются в базе данных.",
                "items": [
                    "создание заявки доступно клиенту;",
                    "назначение исполнителя выполняет администратор или специалист;",
                    "статус отражает текущий этап работ;",
                    "комментарии помогают согласовать детали.",
                ],
            },
            {
                "title": "Файлы и документы",
                "text": "К заявкам можно прикреплять файлы, а по результатам работ формировать документы.",
                "items": [
                    "вложения скачиваются с учетом прав доступа;",
                    "акт выполненных работ формируется в формате DOCX;",
                    "отчеты по заявкам выгружаются в XLSX;",
                    "если файл отсутствует на диске, пользователь получает понятное сообщение.",
                ],
            },
        ],
        "steps": [
            "Клиент регистрируется и создает заявку.",
            "Администратор проверяет обращение и назначает специалиста.",
            "Специалист меняет статус, добавляет комментарии и прикрепляет файлы.",
            "После выполнения специалист формирует акт, а администратор может выгрузить отчет.",
        ],
    },
}


def breadcrumbs(*items):
    trail = [{"label": "Главная", "url": url_for("public.home")}]
    trail.extend(items)
    return trail


@public_bp.route("/")
def home():
    services = Service.query.filter_by(is_active=True).limit(4).all()
    news = (
        Article.query.filter_by(article_type="news", is_published=True)
        .order_by(Article.created_at.desc())
        .limit(3)
        .all()
    )
    stats = {
        "services": Service.query.filter_by(is_active=True).count(),
        "knowledge": Article.query.filter_by(article_type="knowledge", is_published=True).count(),
        "news": Article.query.filter_by(article_type="news", is_published=True).count(),
    }
    return render_template(
        "public/home.html",
        title="Главная",
        services=services,
        news=news,
        stats=stats,
        breadcrumbs=[{"label": "Главная", "url": None}],
    )


@public_bp.route("/services")
def services():
    services_list = Service.query.filter_by(is_active=True).order_by(Service.name).all()
    return render_template(
        "public/services.html",
        title="Услуги",
        services=services_list,
        breadcrumbs=breadcrumbs({"label": "Услуги", "url": None}),
    )


@public_bp.route("/knowledge-base")
def knowledge_base():
    articles = (
        Article.query.filter_by(article_type="knowledge", is_published=True)
        .order_by(Article.created_at.desc())
        .all()
    )
    return render_template(
        "public/articles.html",
        title="База знаний",
        articles=articles,
        page_kind="knowledge",
        lead="Инструкции и регламенты для клиентов, специалистов и администратора сервиса.",
        breadcrumbs=breadcrumbs({"label": "База знаний", "url": None}),
    )


@public_bp.route("/news")
def news():
    articles = (
        Article.query.filter_by(article_type="news", is_published=True)
        .order_by(Article.created_at.desc())
        .all()
    )
    return render_template(
        "public/articles.html",
        title="Новости",
        articles=articles,
        page_kind="news",
        lead="Новости учебного веб-сервиса, изменения в регламентах и заметки о поддержке клиентов.",
        breadcrumbs=breadcrumbs({"label": "Новости", "url": None}),
    )


@public_bp.route("/article/<slug>")
def article_detail(slug):
    article = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    parent_label = "База знаний" if article.article_type == "knowledge" else "Новости"
    parent_url = url_for("public.knowledge_base") if article.article_type == "knowledge" else url_for("public.news")
    return render_template(
        "public/article_detail.html",
        title=article.title,
        article=article,
        breadcrumbs=breadcrumbs(
            {"label": parent_label, "url": parent_url},
            {"label": article.title, "url": None},
        ),
    )


@public_bp.route("/<page_slug>")
def static_page(page_slug):
    page = PUBLIC_PAGES.get(page_slug)
    if page is None:
        return render_template(
            "shared/404.html",
            title="Страница не найдена",
            breadcrumbs=breadcrumbs({"label": "Страница не найдена", "url": None}),
        ), 404
    return render_template(
        "public/static_page.html",
        title=page["title"],
        page=page,
        breadcrumbs=breadcrumbs({"label": page["title"], "url": None}),
    )


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
    return render_template(
        "public/feedback.html",
        title="Обратная связь",
        breadcrumbs=breadcrumbs(
            {"label": "Контакты", "url": url_for("public.static_page", page_slug="contacts")},
            {"label": "Обратная связь", "url": None},
        ),
    )


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
    return render_template(
        "auth/login.html",
        title="Вход",
        breadcrumbs=breadcrumbs({"label": "Вход", "url": None}),
    )


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
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
            role=role,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Client(
                user=user,
                organization_name=organization_name or "Новая организация",
                contact_person=full_name,
            )
        )
        db.session.commit()
        flash("Регистрация выполнена. Теперь можно войти в личный кабинет.", "success")
        return redirect(url_for("public.login"))
    return render_template(
        "auth/register.html",
        title="Регистрация",
        breadcrumbs=breadcrumbs({"label": "Регистрация", "url": None}),
    )


@public_bp.route("/logout")
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("public.home"))
