import uuid
from fastapi import HTTPException, status
from pydantic import UUID4
import regex as re
from sqlalchemy.orm import Session
from app.models import User, Board



# For Simplicity the user is only allowed to provide one first and one last name
def validate_username(name):
    pattern = r"^\p{L}+(\s\p{L}+)?$"
    if re.match(pattern, name):
        return True
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please only provide one first name and one last name")


def validate_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def get_board_from_db(id: UUID4, db: Session, current_user: User):
    board_query = db.query(Board).filter(Board.id == id)
    board = board_query.first()

    check_board_permission(board, current_user)

    return (board_query, board)


def check_board_permission(board: Board | None, current_user: User):
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Couldn't find board with id {id}")

    is_user_contributor = False
    is_user_owner = board.owner_id == current_user.id

    for user in board.contributors:
        if user.id == current_user.id:
            is_user_contributor = True
    
    if not is_user_contributor and not is_user_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this board. Please contact the owner of this board if you wish access.")
