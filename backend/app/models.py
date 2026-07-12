import json
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    can_login: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    tasks_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    agenda_items: Mapped[list["AgendaItem"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    calendar_feeds: Mapped[list["PersonCalendarFeed"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="person")

    task_managers: Mapped[list["TaskManager"]] = relationship(
        foreign_keys="TaskManager.owner_person_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    manages_tasks_for: Mapped[list["TaskManager"]] = relationship(
        foreign_keys="TaskManager.manager_person_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )
    agenda_managers: Mapped[list["AgendaManager"]] = relationship(
        foreign_keys="AgendaManager.owner_person_id",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    manages_agenda_for: Mapped[list["AgendaManager"]] = relationship(
        foreign_keys="AgendaManager.manager_person_id",
        back_populates="manager",
        cascade="all, delete-orphan",
    )
    api_tokens: Mapped[list["PersonApiToken"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class PersonCalendarFeed(Base):
    __tablename__ = "person_calendar_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(String(100), default="")
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    prefix: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    show_times: Mapped[bool] = mapped_column(Boolean, default=False)
    hide_title: Mapped[bool] = mapped_column(Boolean, default=False)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_modified: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    person: Mapped["Person"] = relationship(back_populates="calendar_feeds")
    agenda_items: Mapped[list["AgendaItem"]] = relationship(
        back_populates="feed", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(50), default="default")
    repeat_type: Mapped[str] = mapped_column(String(20), default="daily")
    repeat_weekdays: Mapped[str] = mapped_column(Text, default="[]")
    anchor_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    day_orders: Mapped[list["TaskDayOrder"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    completions: Mapped[list["TaskCompletion"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    person: Mapped["Person | None"] = relationship(back_populates="tasks")

    def get_weekdays(self) -> list[int]:
        try:
            return json.loads(self.repeat_weekdays)
        except (json.JSONDecodeError, TypeError):
            return []


class TaskDayOrder(Base):
    __tablename__ = "task_day_orders"
    __table_args__ = (UniqueConstraint("task_id", "order_date", name="uq_task_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    task: Mapped["Task"] = relationship(back_populates="day_orders")


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    __table_args__ = (UniqueConstraint("task_id", "completion_date", name="uq_task_completion"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    task: Mapped["Task"] = relationship(back_populates="completions")


class TaskManager(Base):
    __tablename__ = "task_managers"
    __table_args__ = (
        UniqueConstraint("owner_person_id", "manager_person_id", name="uq_task_manager_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    manager_person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped["Person"] = relationship(foreign_keys=[owner_person_id], back_populates="task_managers")
    manager: Mapped["Person"] = relationship(foreign_keys=[manager_person_id], back_populates="manages_tasks_for")


class AgendaManager(Base):
    __tablename__ = "agenda_managers"
    __table_args__ = (
        UniqueConstraint("owner_person_id", "manager_person_id", name="uq_agenda_manager_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    manager_person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped["Person"] = relationship(foreign_keys=[owner_person_id], back_populates="agenda_managers")
    manager: Mapped["Person"] = relationship(foreign_keys=[manager_person_id], back_populates="manages_agenda_for")


class AgendaItem(Base):
    __tablename__ = "agenda_items"
    __table_args__ = (
        UniqueConstraint("feed_id", "external_uid", name="uq_feed_external_uid"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    repeat_type: Mapped[str] = mapped_column(String(20), default="daily")
    repeat_weekdays: Mapped[str] = mapped_column(Text, default="[]")
    anchor_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual")
    external_uid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feed_id: Mapped[int | None] = mapped_column(
        ForeignKey("person_calendar_feeds.id", ondelete="CASCADE"), nullable=True
    )
    google_feed_id: Mapped[int | None] = mapped_column(
        ForeignKey("person_google_calendar_feeds.id", ondelete="CASCADE"), nullable=True
    )
    event_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    person: Mapped["Person"] = relationship(back_populates="agenda_items")
    feed: Mapped["PersonCalendarFeed | None"] = relationship(back_populates="agenda_items")
    google_feed: Mapped["PersonGoogleCalendarFeed | None"] = relationship(back_populates="agenda_items")

    def get_weekdays(self) -> list[int]:
        try:
            return json.loads(self.repeat_weekdays)
        except (json.JSONDecodeError, TypeError):
            return []


class AfvalwijzerConfig(Base):
    __tablename__ = "afvalwijzer_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    postcode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    huisnummer: Mapped[str | None] = mapped_column(String(10), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    types: Mapped[list["AfvalwijzerType"]] = relationship(
        back_populates="config", cascade="all, delete-orphan", order_by="AfvalwijzerType.id"
    )


class AfvalwijzerType(Base):
    __tablename__ = "afvalwijzer_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(ForeignKey("afvalwijzer_config.id", ondelete="CASCADE"))
    waste_type: Mapped[str] = mapped_column(String(50), nullable=False)
    type_label: Mapped[str] = mapped_column(String(100), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    naam: Mapped[str] = mapped_column(String(100), default="")
    buiten_dag: Mapped[str] = mapped_column(String(20), default="day_before")
    buiten_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    buiten_icon: Mapped[str] = mapped_column(String(50), default="fas:trash")
    binnen_dag: Mapped[str] = mapped_column(String(20), default="same_day")
    binnen_person_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    binnen_icon: Mapped[str] = mapped_column(String(50), default="fas:trash")

    config: Mapped["AfvalwijzerConfig"] = relationship(back_populates="types")


class GoogleApiConfig(Base):
    __tablename__ = "google_api_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    redirect_uri_override: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class PersonGoogleAuth(Base):
    __tablename__ = "person_google_auth"
    __table_args__ = (UniqueConstraint("person_id", name="uq_person_google_auth"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    google_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    calendar_feeds: Mapped[list["PersonGoogleCalendarFeed"]] = relationship(
        back_populates="google_auth", cascade="all, delete-orphan"
    )


class PersonGoogleCalendarFeed(Base):
    __tablename__ = "person_google_calendar_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    auth_id: Mapped[int] = mapped_column(ForeignKey("person_google_auth.id", ondelete="CASCADE"))
    google_calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    calendar_name: Mapped[str] = mapped_column(String(200), default="")
    calendar_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    color_filters: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    google_auth: Mapped["PersonGoogleAuth"] = relationship(back_populates="calendar_feeds")
    agenda_items: Mapped[list["AgendaItem"]] = relationship(
        back_populates="google_feed", cascade="all, delete-orphan"
    )


class PersonApiToken(Base):
    __tablename__ = "person_api_tokens"
    __table_args__ = (
        UniqueConstraint("person_id", "device_id", name="uq_person_api_token_device"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[str] = mapped_column(String(200), default="Onbekend apparaat")
    device_type: Mapped[str] = mapped_column(String(20), default="mobile")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    person: Mapped["Person"] = relationship(back_populates="api_tokens")


class DashboardUpgrade(Base):
    __tablename__ = "dashboard_upgrades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
