import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import AfvalwijzerConfig, AfvalwijzerType, Task
from app.services.dashboard_service import TaskService

logger = logging.getLogger(__name__)


class AfvalwijzerService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_config(self) -> AfvalwijzerConfig:
        config = self.db.query(AfvalwijzerConfig).first()
        if not config:
            config = AfvalwijzerConfig()
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        return config

    def update_config(
        self, enabled: bool, postcode: str | None, huisnummer: str | None
    ) -> AfvalwijzerConfig:
        config = self.get_or_create_config()
        config.enabled = enabled
        config.postcode = postcode
        config.huisnummer = huisnummer
        self.db.commit()
        self.db.refresh(config)
        return config

    def sync_types(self, types: list[dict]) -> AfvalwijzerConfig:
        """Upsert waste types from mijnafvalwijzer; remove types no longer present."""
        config = self.get_or_create_config()
        existing = {t.waste_type: t for t in config.types}
        incoming = {t["waste_type"]: t for t in types}

        for wt, info in incoming.items():
            if wt in existing:
                existing[wt].type_label = info["label"]
            else:
                self.db.add(AfvalwijzerType(
                    config_id=config.id,
                    waste_type=wt,
                    type_label=info["label"],
                    naam=info["label"],
                ))

        for wt, t in existing.items():
            if wt not in incoming:
                self.db.delete(t)

        self.db.commit()
        self.db.refresh(config)
        return config

    def update_type(self, type_id: int, **kwargs) -> AfvalwijzerType | None:
        t = self.db.query(AfvalwijzerType).filter(AfvalwijzerType.id == type_id).first()
        if not t:
            return None
        for key, value in kwargs.items():
            setattr(t, key, value)
        self.db.commit()
        self.db.refresh(t)
        return t

    def config_to_dict(self, config: AfvalwijzerConfig) -> dict:
        return {
            "id": config.id,
            "enabled": bool(config.enabled),
            "postcode": config.postcode or "",
            "huisnummer": config.huisnummer or "",
            "types": [self.type_to_dict(t) for t in config.types],
        }

    def type_to_dict(self, t: AfvalwijzerType) -> dict:
        return {
            "id": t.id,
            "waste_type": t.waste_type,
            "type_label": t.type_label,
            "enabled": bool(t.enabled),
            "naam": t.naam or "",
            "buiten_dag": t.buiten_dag or "day_before",
            "buiten_person_id": t.buiten_person_id,
            "buiten_icon": t.buiten_icon or "fas:trash",
            "binnen_dag": t.binnen_dag or "same_day",
            "binnen_person_id": t.binnen_person_id,
            "binnen_icon": t.binnen_icon or "fas:trash",
        }

    def create_tasks_for_weeks(self, week_starts: list[date]) -> int:
        """Create buiten/binnen tasks for the given week(s). Returns count of created tasks."""
        from app.services.mijnafvalwijzer import get_schedule

        config = self.get_or_create_config()
        if not config.enabled:
            return 0

        enabled_types = [t for t in config.types if t.enabled]
        if not enabled_types:
            return 0

        if not config.postcode or not config.huisnummer:
            return 0

        all_dates: set[date] = set()
        for week_start in week_starts:
            for i in range(7):
                all_dates.add(week_start + timedelta(days=i))

        if not all_dates:
            return 0

        min_date = min(all_dates)
        max_date = max(all_dates)

        schedule = get_schedule(
            config.postcode,
            config.huisnummer,
            from_date=min_date - timedelta(days=1),
            to_date=max_date + timedelta(days=1),
        )

        task_service = TaskService(self.db)
        count = 0

        for event in schedule:
            pickup_date: date = event["date"]
            waste_type: str = event["waste_type"]

            for afval_type in enabled_types:
                if afval_type.waste_type != waste_type:
                    continue

                naam = (afval_type.naam or afval_type.type_label or "").strip()
                if not naam:
                    continue

                # Buiten zetten task
                if afval_type.buiten_person_id:
                    buiten_date = (
                        pickup_date - timedelta(days=1)
                        if afval_type.buiten_dag == "day_before"
                        else pickup_date
                    )
                    if buiten_date in all_dates:
                        title = f"{naam} buitenzetten"
                        if not self._task_exists(afval_type.buiten_person_id, title, buiten_date):
                            task_service.create({
                                "person_id": afval_type.buiten_person_id,
                                "title": title[:200],
                                "description": f"Zet de {naam} buiten",
                                "icon": afval_type.buiten_icon or "fas:trash",
                                "repeat_type": "once",
                                "repeat_weekdays": "[]",
                                "anchor_date": buiten_date,
                                "start_date": None,
                                "end_date": None,
                                "sort_order": 0,
                            })
                            count += 1

                # Binnen zetten task
                if afval_type.binnen_person_id:
                    binnen_date = (
                        pickup_date + timedelta(days=1)
                        if afval_type.binnen_dag == "day_after"
                        else pickup_date
                    )
                    if binnen_date in all_dates:
                        title = f"{naam} binnenzetten"
                        if not self._task_exists(afval_type.binnen_person_id, title, binnen_date):
                            task_service.create({
                                "person_id": afval_type.binnen_person_id,
                                "title": title[:200],
                                "description": f"Breng {naam} naar binnen",
                                "icon": afval_type.binnen_icon or "fas:trash",
                                "repeat_type": "once",
                                "repeat_weekdays": "[]",
                                "anchor_date": binnen_date,
                                "start_date": None,
                                "end_date": None,
                                "sort_order": 0,
                            })
                            count += 1

        return count

    def _task_exists(self, person_id: int, title: str, anchor_date: date) -> bool:
        return (
            self.db.query(Task)
            .filter(
                Task.person_id == person_id,
                Task.title == title,
                Task.anchor_date == anchor_date,
            )
            .first()
            is not None
        )
