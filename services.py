import os as _os
from time import sleep
import dotenv as _dotenv
import jwt as _jwt
import sqlalchemy.orm as _orm
import passlib.hash as _hash
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import datetime as _dt
import database as _database
import schemas as _schemas
import models as _models
from concurrent.futures import ThreadPoolExecutor

import email_send

from fastapi.security import HTTPBasic, HTTPBasicCredentials

_dotenv.load_dotenv()

_JWT_SECRET = _os.environ['JWT_SECRET']
MINUTES = int(_os.environ['MINUTES'])

oauth2schema = _security.OAuth2PasswordBearer("/api/token")

security = HTTPBasic()

def create_database():
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_by_email(email: str, db: _orm.Session):
    return db.query(_models.User).filter(_models.User.email == email).first()

async def create_user(user: _schemas.UserCreate, db: _orm.Session):

    try:
        valid = _email_check.validate_email(email=user.email)

        email = valid.email
    except _email_check.EmailNotValidError:
        raise _fastapi.HTTPException(status_code=404, detail="Please enter a valid email")

    user_obj = _models.User(email=email, hashed_password=_hash.bcrypt.hash(user.password))

    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

async def authenticate_user(email: str, password: str, db: _orm.Session):
    user = await get_user_by_email(email=email, db=db)

    if not user:
        return False
    
    if not user.verify_password(password):
        return False

    return user

async def create_token(user: _models.User):
    user_obj = _schemas.User.from_orm(user)

    user_dict = user_obj.dict()
    del user_dict["date_created"]
    user_dict["exp"] = _dt.datetime.utcnow() + _dt.timedelta(days=1, minutes=1)
    user_dict["iat"] =  _dt.datetime.utcnow()

    token = _jwt.encode(user_dict, _JWT_SECRET)

    return dict(access_token=token, token_type="bearer", admin=user_obj.admin, email = user_obj.email)


async def get_current_user(db: _orm.Session = _fastapi.Depends(get_db), token: str = _fastapi.Depends(oauth2schema)):

    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    
    except:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Email or Password"
        )
    return _schemas.User.from_orm(user)

async def get_user_list(db: _orm.Session):
    return db.query(_models.User).filter(_models.User.admin == False).all()

async def delete_user(db: _orm.Session, id: int):
    db_item = db.query(_models.User).get(id)
    db.delete(db_item)
    db.commit()
    return db_item

def edit_user(db: _orm.Session, item: _schemas.UserEdit, id : int):
    db_item = db.query(_models.User).get(id)
    if _hash.bcrypt.verify(item.old_password, db_item.hashed_password) == False:
        raise _fastapi.HTTPException(status_code=401, detail="Please enter correct password")
    if item.email:
        db_item.email = item.email
    db_item.hashed_password = _hash.bcrypt.hash(item.password)
    db.commit()
    db.refresh(db_item)
    return db_item

# Arduino CRUD services

def arduino_get(db: _orm.Session, skip: int = 0, limit: int = 100):
    return db.query(_models.Arduino).offset(skip).limit(limit).all()


def create_arduino(db: _orm.Session, item: _schemas.ArduinoCreate):
    db_item = _models.Arduino(arduinoname=item.arduinoname, password_hash=_hash.bcrypt.hash(item.password_hash))
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_arduino(db: _orm.Session, id: int):
    db_item = db.query(_models.Arduino).get(id)
    db.delete(db_item)
    db.commit()
    return db_item

# Freezer CRUD services

def freezer_get(db: _orm.Session, id: int):
    return db.query(_models.Freezer).filter(_models.Freezer.arduino_id == id).all()


def create_freezer(db: _orm.Session, item: _schemas.FreezerCreate):
    db_item = _models.Freezer(name=item.name, arduino_id=item.arduino_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_freezer(db: _orm.Session, id: int):
    db_item = db.query(_models.Freezer).get(id)
    db.delete(db_item)
    db.commit()
    return db_item

# Temperature Reads CRUD & Authentication Services

def authenticate_temp_post(credentials: HTTPBasicCredentials = _fastapi.Depends(security),
    db: _orm.Session = _fastapi.Depends(get_db)):
    try:
        arduino_ins = db.query(_models.Arduino).filter(_models.Arduino.arduinoname == credentials.username).first()
        correct_password = arduino_ins.verify_password(credentials.password)

        if not (arduino_ins and correct_password):
            raise _fastapi.HTTPException(
                status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Basic"},
            )

        return credentials.username
    except:
        raise _fastapi.HTTPException(
                status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Basic"},
            )

def temp_get(db: _orm.Session, id: int):
    return db.query(_models.Temperature).filter(_models.Temperature.freeze_id == id).all()


def create_temp(db: _orm.Session, item: _schemas.TemperatureCreate):
    db_item = _models.Temperature(freeze_id=item.freeze_id, temperature=item.temperature)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_temp(db: _orm.Session, id: int):
    db.query(_models.Temperature).filter(_models.Temperature.freeze_id == id).delete(synchronize_session=False)
    db.commit()
    return

_threadpool_cpus = int(_os.cpu_count() / 2)
EXECUTOR = ThreadPoolExecutor(max_workers=max(_threadpool_cpus, 2))


def minutes_ago():
    return _dt.datetime.utcnow() - _dt.timedelta(minutes = MINUTES)

async def email_alarm_user():
    freezers = next(get_db()).query(_models.Freezer).all()
    for freezer in freezers:
        max_temp = freezer.max_temp
        temps = next(get_db()).query(_models.Temperature).filter(
            _models.Temperature.freeze_id == freezer.id, 
            _models.Temperature.reading_date > minutes_ago())
        for temp in temps:
            if temp.temperature > max_temp:
                EXECUTOR.submit(concurrent_check_freezer(freezer.id, max_temp, freezer.name))
                pass
    return 0

#Concurrent Function that checks temperature again after an hour
def concurrent_check_freezer(freezer_id,  max_temp, freezer_name):
    sleep(MINUTES * 60)
    temps = next(get_db()).query(_models.Temperature).filter(
            _models.Temperature.freeze_id == freezer_id, 
            _models.Temperature.reading_date > minutes_ago())
    for temp in temps:
        if temp.temperature > max_temp:
            email_send.sendEmail(freezer_id, freezer_name)

def delete_temp_data_every_period():
    next(get_db()).query(_models.Temperature).all().delete(synchronize_session=False)
    next(get_db()).commit()
    return 0