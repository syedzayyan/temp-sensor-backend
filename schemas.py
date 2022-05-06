import datetime as _dt
from typing import Optional
import pydantic as _pydantic

class _UserBase(_pydantic.BaseModel):
    email: str

class UserCreate(_UserBase):
    password: str

    class Config:
        orm_mode = True

class UserEdit(_UserBase):
    email: Optional[str]
    password: str
    old_password: str

    class Config:
        orm_mode = True
class User(_UserBase):
    id: int
    date_created: _dt.datetime
    admin: bool

    class Config:
        orm_mode = True


class ArduinoBase(_pydantic.BaseModel):
    arduinoname: str

class ArduinoCreate(ArduinoBase):
    password_hash: str

class Arduino(ArduinoBase):
    id : int
    class Config:
        orm_mode = True

# Freezer Schemas

class FreezerBase(_pydantic.BaseModel):
    name: str
    arduino_id: str
    max_temp: int


class FreezerCreate(FreezerBase):
    pass


class Freezer(FreezerBase):
    id: int

    class Config:
        orm_mode = True

# Temp Reading Schemas

class TemperatureBase(_pydantic.BaseModel):
    temperature: int


class TemperatureCreate(TemperatureBase):
    freeze_id: int

class Temperature(TemperatureBase):
    reading_date: _dt.datetime

    class Config:
        orm_mode = True