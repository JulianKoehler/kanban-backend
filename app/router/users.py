from operator import or_
from typing import List
from urllib.parse import unquote
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pydantic import UUID4
from sqlalchemy import exc, func
from sqlalchemy.orm import Session
from app.oauth2 import create_access_token, get_current_user
from app.database import get_db
from app.schemas import UserContributingUpdate, UserCreate, UserInfoReturn, UserReturn
from app.models import Board, User
from app.utils.helpers import getFirstAndLastName, hash
from app.utils.validation import get_board_from_db


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/current", response_model=UserInfoReturn)
def get_current_user_data(current_user: User = Depends(get_current_user)):

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Please login")

    return current_user


@router.get("/", response_model=List[UserReturn])
def get_users(q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if not q:
        return JSONResponse(content=[])

    query = unquote(q).lower()

    users = db.query(User).filter(User.id != current_user.id, or_(func.lower(User.first_name).startswith(
        query), or_(func.lower(User.last_name).startswith(query), func.lower(User.email) == query))).all()

    return users


@router.get("/{id}", response_model=UserReturn)
def get_user(id: UUID4, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == id).first()

    print(user)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id {id} does not exist")

    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserReturn)
def create_user(client_data: UserCreate, response: Response,  db: Session = Depends(get_db)):

    user_data = transform_client_data(client_data)
    new_user = User(**user_data)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except exc.SQLAlchemyError as e:
        db.rollback()
        error_message = str(e)
        print(error_message)
        if "unique-constraint" in error_message.lower() or "unique constraint" in error_message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Email '{client_data.email}' already in use.")
        else:
            print(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Database error, please check the server logs.")

    access_token = create_access_token({"user_id": str(new_user.id)})

    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, secure=True, samesite='none')

    return new_user


@router.put("/", status_code=status.HTTP_204_NO_CONTENT)
def stop_contributing_to_board(client_data: UserContributingUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(client_data.board_id, db, current_user)

    current_user.boards_contributing.remove(board)

    db.commit()

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    has_boards = db.query(Board).filter(
        Board.owner_id == current_user.id).first()

    if has_boards:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail='Delete all of your boards before you delete your account.')

    # TODO Später wenn man User zu seinen Boards hinzufügen kann, soll der User bevor er seinen Account löscht für jedes seiner Boards einen neuen Owner festlegen!

    db.query(User).filter(User.id == current_user.id).delete()
    db.commit()


def transform_client_data(data: UserCreate):
    (first_name, last_name) = getFirstAndLastName(data.user_name)

    user = data.model_dump()
    del user["user_name"]
    user["first_name"] = first_name
    user["last_name"] = last_name
    user["password"] = hash(data.password)

    return user
