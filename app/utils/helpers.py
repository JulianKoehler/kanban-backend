from app.schemas import StageBase
from .validation import validate_username
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def getFirstAndLastName(name: str):
    validate_username(name) # Making sure we are only dealing with 1 first and 1 lastname seperated by a space
    name_array = name.split(" ")
    first_name = name_array[0]
    last_name: str | None
    if len(name_array) < 2:
        last_name = None
    else:
        last_name = name_array[1]

    return (first_name, last_name)


def hash(password: str):
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_index(stage: StageBase):
    return stage.index
