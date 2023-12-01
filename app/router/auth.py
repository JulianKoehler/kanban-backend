from datetime import timedelta
from typing_extensions import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import UUID4
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database import get_db
from app.models import User
from app.oauth2 import create_access_token, verify_access_token
from app.schemas import NewUserPassword, UserPasswordResetRequest, UserInfoReturn
from app.utils.helpers import verify, hash
from app.email_service import auth_email_service

import os
from dotenv import load_dotenv


loaded = load_dotenv(".env.local")
IS_DEV = os.getenv('IS_DEV')


router = APIRouter(tags=["Authentication"])


@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserInfoReturn)
def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response,
          db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect e-mail")

    if not verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    access_token = create_access_token({"user_id": str(user.id)})

    response.set_cookie(key="access_token",
                        value=f"Bearer {access_token}", httponly=True)

    return user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response):
    response.delete_cookie("access_token", httponly=True)

    return {"message": "Logout successful"}


@router.post("/password/request-reset")
async def send_password_reset_email(client_data: UserPasswordResetRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == client_data.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with email {client_data.email} found')

    reset_link = generate_reset_link(user.id)

    result = await auth_email_service.password_forgotten(recipient=client_data.email, reset_link=reset_link)
    has_errors = len(result) > 0

    if has_errors:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Could not send email. Please try again later.")
    

@router.post('/password/new', status_code=status.HTTP_201_CREATED)
def update_password(client_data: NewUserPassword, response: Response, db: Session = Depends(get_db)):
    token_data = verify_access_token(client_data.access_token)

    user_query = db.query(User).filter(User.id == token_data.user_id)
    user = user_query.first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_password = hash(client_data.password)
    user_query.update({ 'password': new_password})
    
    db.commit()

    access_token = create_access_token({ "user_id": str(user.id) })

    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)



def generate_reset_link(id: UUID4):
    pwd_reset_token = create_access_token(
        data={'user_id': str(id)}, expires_delta=timedelta(minutes=5))
    BASE_URL = 'http://localhost:3000/' if IS_DEV else 'https://kanban-board-jet.vercel.app/'
    # If you change the name of the query param, make sure to adjust the frontend code
    reset_link = f'{BASE_URL}/new-password?token={pwd_reset_token}'

    return reset_link
