import datetime
from peewee import CharField, IntegerField, DateTimeField
from app.database import BaseModel, db


class ErrorLog(BaseModel):
    time = DateTimeField(default=datetime.datetime.utcnow)
    status = IntegerField()
    error = CharField(max_length=500)
    method = CharField(max_length=10, default="")
    path = CharField(max_length=500, default="")


def record_error(status, error, method="", path=""):
    try:
        ErrorLog.create(
            status=status,
            error=str(error)[:500],
            method=method,
            path=path,
        )
        # Keep only the latest 200 entries
        cutoff = ErrorLog.select(ErrorLog.id).order_by(ErrorLog.id.desc()).offset(200).limit(1).scalar()
        if cutoff:
            ErrorLog.delete().where(ErrorLog.id <= cutoff).execute()
    except Exception:
        pass  # Never let logging break the request


def get_errors(limit=50):
    try:
        rows = (ErrorLog
                .select()
                .order_by(ErrorLog.id.desc())
                .limit(limit))
        return [{
            "time": r.time.strftime("%H:%M:%S"),
            "status": r.status,
            "error": r.error,
            "method": r.method,
            "path": r.path,
        } for r in rows]
    except Exception:
        return []
