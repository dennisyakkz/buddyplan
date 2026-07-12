import os

from sqlalchemy.orm import Session

from app.models import Person, Task
from app.services.dashboard_service import PersonService


def _bootstrap_from_env(db: Session) -> None:
    username = os.environ.get("BUDDYPLAN_ADMIN_USERNAME", "").strip()
    password = os.environ.get("BUDDYPLAN_ADMIN_PASSWORD", "").strip()
    name = os.environ.get("BUDDYPLAN_ADMIN_NAME", "Admin").strip() or "Admin"
    if not username or not password:
        return
    PersonService(db).bootstrap_admin(name, username, password)


def seed_database(db: Session) -> None:
    if not PersonService(db).has_login_users():
        _bootstrap_from_env(db)

    orphan_tasks = db.query(Task).filter(Task.person_id.is_(None)).all()
    if orphan_tasks:
        default_owner = (
            db.query(Person)
            .filter(Person.tasks_enabled.is_(True))
            .order_by(Person.sort_order, Person.id)
            .first()
        ) or db.query(Person).order_by(Person.sort_order, Person.id).first()
        if default_owner:
            for task in orphan_tasks:
                task.person_id = default_owner.id

    db.commit()
