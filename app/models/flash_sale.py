import datetime
from peewee import CharField, IntegerField, ForeignKeyField, DateTimeField
from app.database import BaseModel

class Event(BaseModel):
    name = CharField(unique=True)
    total_tickets = IntegerField()
    available_tickets = IntegerField()

class Reservation(BaseModel):
    event = ForeignKeyField(Event, backref='reservations')
    user_email = CharField()
    reserved_at = DateTimeField(default=datetime.datetime.now)
