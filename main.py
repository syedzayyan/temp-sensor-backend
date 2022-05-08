from typing import List
import fastapi as _fastapi
import fastapi.security as _security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic
from fastapi_utils.tasks import repeat_every
import sqlalchemy.orm as _orm
import services as _services
import schemas as _schemas

import os as _os
import dotenv as _dotenv

app = _fastapi.FastAPI()
security = HTTPBasic()


_dotenv.load_dotenv()

FRONT_URL = _os.environ['FRONTEND_URL']

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5000",
    FRONT_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/users")
async def create_user(user: _schemas.UserCreate, db: _orm.Session = _fastapi.Depends(_services.get_db), 
    user_data: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    if user_data.admin == False:
        raise _fastapi.HTTPException(
            status_code=401, detail = "Only Admin Users"
        )
    db_user = await _services.get_user_by_email(email=user.email, db=db)
    if db_user:
        raise _fastapi.HTTPException(
            status_code=400,
            detail="User with that email already exists")

    user = await _services.create_user(user=user, db=db)

    return await _services.create_token(user=user)

@app.get("/api/users", response_model=list[_schemas.User])
async def get_user(db: _orm.Session = _fastapi.Depends(_services.get_db),
    user_data: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    if user_data.admin == False:
        raise _fastapi.HTTPException(
            status_code=401, detail = "Only Admin Users"
        )
    return await _services.get_user_list(db=db)

@app.put("/api/users/")
async def edit_user(item: _schemas.UserEdit, db: _orm.Session = _fastapi.Depends(_services.get_db),
    user_data: _schemas.User = _fastapi.Depends(_services.get_current_user)):

    return _services.edit_user(db=db, id=user_data.id, item=item)

@app.delete("/api/users/{id}")
async def delete_user(id : int, db: _orm.Session = _fastapi.Depends(_services.get_db),
    user_data: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    if user_data.admin == False:
        raise _fastapi.HTTPException(
            status_code=401, detail = "Only Admin Users"
        )
    return await _services.delete_user(db=db, id=id)

@app.post("/api/token")
async def generate_token(form_data: _security.OAuth2PasswordRequestForm = _fastapi.Depends(), db: _orm.Session = _fastapi.Depends(_services.get_db)):
    user = await _services.authenticate_user(email=form_data.username, password=form_data.password, db=db)

    if not user:
        raise _fastapi.HTTPException(
            status_code=401, detail="Invalid Credentials")

    return await _services.create_token(user=user)


@app.get("/api/users/me", response_model=_schemas.User)
async def get_user(user: _schemas.User = _fastapi.Depends(_services.get_current_user)):
    return user

# Arduino CRUD Routes
@app.post("/arduino", response_model=_schemas.Arduino)
def create_arduino_api_keys(
    item: _schemas.ArduinoCreate, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
):
    return _services.create_arduino(db=db, item=item)


@app.get("/arduino", response_model=list[_schemas.Arduino])
def read_arduino_names_in_the_database(skip: int = 0, limit: int = 100, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
    ):
    arduinos = _services.arduino_get(db, skip=skip, limit=limit)
    return arduinos

@app.delete("/arduino/{id}")
def delete_arduino_api_keys(
    id: str, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
):
    return _services.delete_arduino(db=db, id=id)

# Freezer CRUD Routes
@app.post("/freezer", response_model=_schemas.Freezer)
def create_freezer_endpoints_for_each_arduino(
    item: _schemas.FreezerCreate, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
):
    return _services.create_freezer(db=db, item=item)


@app.get("/freezer/{id}", response_model=list[_schemas.Freezer])
def read_freezers_in_database(
    id: int, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
    ):
    freezer = _services.freezer_get(db, id=id)
    return freezer

@app.delete("/freezer/{id}")
def delete_freezers(
    id: str, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
):
    return _services.delete_freezer(db=db, id=id)

# Temperature Routes
@app.post("/tempspost", response_model=_schemas.Temperature)
def log_temperatures(
    item: _schemas.TemperatureCreate,
    db: _orm.Session = _fastapi.Depends(_services.get_db), 
    username: str = _fastapi.Depends(_services.authenticate_temp_post)):
    print (username)
    return _services.create_temp(db=db, item=item)


@app.get("/temperature", response_model=list[_schemas.Temperature])
def read_temperatures(id: int, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
    ):
    freezer = _services.temp_get(id = id, db = db)
    return freezer

@app.delete("/temperature/{id}")
def delete_temps_by_freezer_id(
    id: str, db: _orm.Session = _fastapi.Depends(_services.get_db),
    dependencies=_fastapi.Depends(_services.get_current_user)
):
    return _services.delete_temp(db=db, id=id)

@app.on_event("startup")
@repeat_every(seconds=3600)  # 1 hour
async def remove_expired_tokens_task():
    return await _services.email_alarm_user()

@app.on_event("startup")
@repeat_every(seconds=2629746)  # 1 month
def remove_expired_tokens_task():
    return _services.delete_temp_data_every_period()