from typing_extensions import Annotated
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from app.utils.fastapi import OAuth2PasswordBearerWithCookie
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import TokenData


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="login")


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail="Could not validate token", 
                                          headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    return token_data


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    token = verify_access_token(token)
    user = db.query(User).filter(User.id == token.user_id).first()

    return user