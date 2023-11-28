from typing_extensions import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database import get_db
from app.models import User
from app.oauth2 import create_access_token
from app.schemas import Token, UserInfoReturn, UserReturn
from app.utils.helpers import verify

import os
from dotenv import load_dotenv


loaded = load_dotenv(".env.local")
IS_DEV = os.getenv('IS_DEV')


router = APIRouter(tags=["Authentication"])

@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserInfoReturn)
def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response, 
          db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect e-mail")
    
    if not verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    
    access_token = create_access_token({ "user_id": str(user.id)})

    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    
    return user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response):
    response.delete_cookie("access_token", httponly=True)

    return { "message": "Logout successful"}