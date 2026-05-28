from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    users = db.relationship("User", back_populates="role")

    def __repr__(self):
        return self.name


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", back_populates="users")

    client = db.relationship("Client", back_populates="user", uselist=False)
    employee = db.relationship("Employee", back_populates="user", uselist=False)
    comments = db.relationship("TicketComment", back_populates="author")

    @property
    def is_active(self):
        return self.is_active_account

    def has_role(self, *role_names):
        return self.role and self.role.name in role_names

    def __repr__(self):
        return self.full_name


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(180), nullable=False)
    inn = db.Column(db.String(20))
    address = db.Column(db.String(255))
    contact_person = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="client")
    tickets = db.relationship("Ticket", back_populates="client")

    def __repr__(self):
        return self.organization_name


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="employee")
    assigned_tickets = db.relationship("Ticket", back_populates="specialist")

    def __repr__(self):
        return self.user.full_name


class ServiceCategory(db.Model):
    __tablename__ = "service_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)

    services = db.relationship("Service", back_populates="category")

    def __repr__(self):
        return self.name


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)

    category_id = db.Column(db.Integer, db.ForeignKey("service_categories.id"), nullable=False)
    category = db.relationship("ServiceCategory", back_populates="services")
    tickets = db.relationship("Ticket", back_populates="service")

    def __repr__(self):
        return self.name


class TicketStatus(db.Model):
    __tablename__ = "ticket_statuses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    tickets = db.relationship("Ticket", back_populates="status")

    def __repr__(self):
        return self.name


class TicketPriority(db.Model):
    __tablename__ = "ticket_priorities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    response_hours = db.Column(db.Integer, default=24)

    tickets = db.relationship("Ticket", back_populates="priority")

    def __repr__(self):
        return self.name


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)

    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    specialist_id = db.Column(db.Integer, db.ForeignKey("employees.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("ticket_statuses.id"), nullable=False)
    priority_id = db.Column(db.Integer, db.ForeignKey("ticket_priorities.id"), nullable=False)

    client = db.relationship("Client", back_populates="tickets")
    specialist = db.relationship("Employee", back_populates="assigned_tickets")
    service = db.relationship("Service", back_populates="tickets")
    status = db.relationship("TicketStatus", back_populates="tickets")
    priority = db.relationship("TicketPriority", back_populates="tickets")
    comments = db.relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    attachments = db.relationship("Attachment", back_populates="ticket", cascade="all, delete-orphan")
    documents = db.relationship("Document", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"#{self.id} {self.title}"


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="comments")
    author = db.relationship("User", back_populates="comments")


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="attachments")
    uploaded_by = db.relationship("User")


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    document_type = db.Column(db.String(80), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", back_populates="documents")
    created_by = db.relationship("User")


class FeedbackMessage(db.Model):
    __tablename__ = "feedback_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Article(db.Model):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    summary = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    article_type = db.Column(db.String(50), default="knowledge")
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return self.title
