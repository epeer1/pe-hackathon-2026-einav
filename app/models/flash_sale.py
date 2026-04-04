import datetime
from peewee import CharField, IntegerField, BooleanField, ForeignKeyField, DateTimeField, CompositeKey
from app.database import BaseModel

class Event(BaseModel):
    name = CharField(unique=True)
    total_tickets = IntegerField()
    available_tickets = IntegerField()
    active = BooleanField(default=True)

class Reservation(BaseModel):
    event = ForeignKeyField(Event, backref='reservations')
    user_email = CharField()
    reserved_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        indexes = (
            (('event', 'user_email'), True),  # Unique together: one reservation per user per event
        )

