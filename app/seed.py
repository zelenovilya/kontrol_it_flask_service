from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import db
from app.models import (
    Role, User, Client, Employee, ServiceCategory, Service,
    TicketStatus, TicketPriority, Ticket, TicketComment, Article
)


def init_db():
    db.create_all()

    if Role.query.count() > 0:
        return

    admin_role = Role(name="Администратор", description="Полный доступ к управлению сервисом")
    specialist_role = Role(name="Специалист", description="Обработка и выполнение заявок")
    client_role = Role(name="Клиент", description="Создание заявок и просмотр своих обращений")
    db.session.add_all([admin_role, specialist_role, client_role])
    db.session.flush()

    admin = User(
        username="admin",
        password_hash=generate_password_hash("admin123", method="pbkdf2:sha256"),
        email="admin@kontrol-it.local",
        full_name="Администратор системы",
        phone="+7 900 000-00-01",
        role=admin_role,
    )
    specialist_user = User(
        username="specialist",
        password_hash=generate_password_hash("spec123", method="pbkdf2:sha256"),
        email="specialist@kontrol-it.local",
        full_name="Иванов Сергей Петрович",
        phone="+7 900 000-00-02",
        role=specialist_role,
    )
    client_user = User(
        username="client",
        password_hash=generate_password_hash("client123", method="pbkdf2:sha256"),
        email="client@example.local",
        full_name="Петров Алексей Николаевич",
        phone="+7 900 000-00-03",
        role=client_role,
    )
    db.session.add_all([admin, specialist_user, client_user])
    db.session.flush()

    employee = Employee(
        user=specialist_user,
        position="Ведущий специалист технической поддержки",
        department="Отдел сопровождения клиентов",
        qualification="Сетевое администрирование, сопровождение рабочих мест",
    )
    client = Client(
        user=client_user,
        organization_name="ООО «Демо-Клиент»",
        inn="7700000000",
        address="г. Москва, ул. Примерная, д. 1",
        contact_person="Петров Алексей Николаевич",
    )
    db.session.add_all([employee, client])

    categories = [
        ServiceCategory(name="Техническая поддержка", description="Оперативное решение пользовательских инцидентов"),
        ServiceCategory(name="Администрирование", description="Сопровождение серверов, рабочих станций и сетевой инфраструктуры"),
        ServiceCategory(name="Информационная безопасность", description="Проверка доступа, резервное копирование, базовая защита"),
    ]
    db.session.add_all(categories)
    db.session.flush()

    services = [
        Service(name="Настройка рабочего места", description="Подключение пользователя, ПО, принтера и сетевых ресурсов", price=2500, category=categories[0]),
        Service(name="Удаленная диагностика инцидента", description="Проверка проблемы через удаленное подключение", price=1500, category=categories[0]),
        Service(name="Настройка резервного копирования", description="Подготовка расписания и проверка восстановления", price=5000, category=categories[2]),
        Service(name="Сопровождение серверов", description="Обновление, мониторинг и регламентное обслуживание", price=12000, category=categories[1]),
        Service(name="Аудит учетных записей", description="Проверка ролей, прав доступа и неактивных пользователей", price=7000, category=categories[2]),
    ]
    db.session.add_all(services)

    statuses = [
        TicketStatus(name="Новая", sort_order=1),
        TicketStatus(name="Принята", sort_order=2),
        TicketStatus(name="В работе", sort_order=3),
        TicketStatus(name="Ожидает клиента", sort_order=4),
        TicketStatus(name="Выполнена", sort_order=5),
        TicketStatus(name="Закрыта", sort_order=6),
    ]
    priorities = [
        TicketPriority(name="Низкий", response_hours=48),
        TicketPriority(name="Средний", response_hours=24),
        TicketPriority(name="Высокий", response_hours=8),
    ]
    db.session.add_all(statuses + priorities)
    db.session.flush()

    ticket = Ticket(
        title="Не открывается корпоративная почта",
        description="При входе в почтовый ящик появляется сообщение об ошибке авторизации.",
        client=client,
        specialist=employee,
        service=services[1],
        status=statuses[2],
        priority=priorities[1],
        deadline_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.session.add(ticket)
    db.session.flush()

    db.session.add(TicketComment(ticket=ticket, author=client_user, text="Проблема повторяется после перезагрузки компьютера."))
    db.session.add(TicketComment(ticket=ticket, author=specialist_user, text="Заявка принята, выполняется проверка учетной записи."))

    articles = [
        Article(title="Как правильно создать заявку", slug="how-to-create-ticket", summary="Краткая инструкция для клиентов", content="Опишите проблему, выберите услугу и при необходимости прикрепите файл.", article_type="knowledge"),
        Article(title="Регламент обработки обращений", slug="ticket-processing-rules", summary="Основные статусы и сроки", content="Заявки проходят статусы от новой до закрытой. Срок реакции зависит от приоритета.", article_type="knowledge"),
        Article(title="ООО «Контроль ИТ» запускает клиентский сервис", slug="service-launch", summary="Новость о внедрении веб-сервиса", content="Единый сервис повышает прозрачность обработки заявок и упрощает контроль работ.", article_type="news"),
    ]
    db.session.add_all(articles)
    db.session.commit()
