import datetime as _dt
from email.policy import default

import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import passlib.hash as _hash

import database as _database


class User(_database.Base):
    __tablename__ = "users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String, unique=True, index=True)
    hashed_password = _sql.Column(_sql.String)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    admin = _sql.Column(_sql.Boolean, default = False)

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)

class Arduino(_database.Base):
    __tablename__ = "arduinolist"
    id = _sql.Column(_sql.Integer, primary_key = True, index = True)
    arduinoname = _sql.Column(_sql.String, unique = True)
    password_hash = _sql.Column(_sql.String)

    freezers = _orm.relationship("Freezer", back_populates="freezer", cascade="all, delete",)

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.password_hash)

class Freezer(_database.Base):
    __tablename__ = "freezer"
    id = _sql.Column(_sql.Integer, primary_key = True, index = True)
    name = _sql.Column(_sql.String, unique = False)
    arduino_id = _sql.Column(_sql.Integer, _sql.ForeignKey("arduinolist.id", ondelete="CASCADE"))
    max_temp = _sql.Column(_sql.Integer, default = 10)

    freezer = _orm.relationship("Arduino", back_populates="freezers")

    temps = _orm.relationship("Temperature", back_populates="freezers_temp")

class Temperature(_database.Base):
    __tablename__ = "temperature_readings"
    id = _sql.Column(_sql.Integer, primary_key = True, index = True)
    freeze_id = _sql.Column(_sql.Integer, _sql.ForeignKey("freezer.id"), unique = False)
    temperature = _sql.Column(_sql.Integer, unique = False)
    reading_date = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)

    freezers_temp = _orm.relationship("Freezer", back_populates="temps")

