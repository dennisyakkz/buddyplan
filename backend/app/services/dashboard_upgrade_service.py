from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import DATA_DIR
from app.models import DashboardUpgrade


class DashboardUpgradeService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def storage_dir() -> Path:
        path = DATA_DIR / "dashboard-upgrade"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_latest(self) -> DashboardUpgrade | None:
        return (
            self.db.query(DashboardUpgrade)
            .order_by(DashboardUpgrade.version.desc())
            .first()
        )

    def get_info(self) -> dict:
        latest = self.get_latest()
        if not latest:
            return {"version": 0, "uploaded_at": None}
        return {
            "version": latest.version,
            "uploaded_at": latest.uploaded_at.isoformat() if latest.uploaded_at else None,
        }

    def upload_apk(self, content: bytes, filename: str) -> DashboardUpgrade:
        if not filename.lower().endswith(".apk"):
            raise ValueError("Alleen APK-bestanden zijn toegestaan")
        if len(content) < 4 or content[:2] != b"PK":
            raise ValueError("Ongeldig APK-bestand")

        max_version = self.db.query(func.max(DashboardUpgrade.version)).scalar() or 0
        new_version = max_version + 1

        storage = self.storage_dir()
        apk_path = storage / "latest.apk"
        temp_path = storage / "latest.apk.tmp"
        temp_path.write_bytes(content)
        temp_path.replace(apk_path)

        record = DashboardUpgrade(version=new_version, file_path=str(apk_path))
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_apk_path(self) -> Path | None:
        latest = self.get_latest()
        if not latest:
            return None
        path = Path(latest.file_path)
        if path.is_file():
            return path
        fallback = self.storage_dir() / "latest.apk"
        return fallback if fallback.is_file() else None
