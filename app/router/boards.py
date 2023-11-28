from typing import List

from pydantic import UUID4
from app.database import get_db
from app.router.stages import create_new_stage, delete_stage, update_stages
from app.schemas import BoardCreateResponse, BoardDataReturn, BoardListReturn, BoardCreate, BoardUpdate, StageCreate, StageUpdate
from app.models import Task, User, Board
from app.oauth2 import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Response, status
from app.utils.helpers import get_index

from app.utils.validation import get_board_from_db


router = APIRouter(prefix="/boards", tags=["Boards"])

@router.get("/", response_model=BoardListReturn)
def get_users_boards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # Easiest way is to simply get the user from the database since our Model holds a direct relationship to all boards that the user is owning or contributing to.
    user = db.query(User).filter(User.id == current_user.id).first()

    return { "own_boards": user.own_boards, "contributing": user.boards_contributing }    


@router.get("/{id}", response_model=BoardDataReturn)
def get_board_data(id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    (board_query, board) = get_board_from_db(id, db, current_user)

    stages = board.stages
    stages.sort(key=get_index)

    return board


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BoardCreateResponse)
def create_board(board: BoardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # Transform the client data a little
    board_data = board.model_dump()
    board_data.update({ "owner_id": (current_user.id) })
    stages: List[StageCreate] = board_data.pop("stages")

    new_board = Board(**board_data)

    db.add(new_board)
    db.commit()
    db.refresh(new_board)

    # After board creation we can access its ID to create the stages with the fkey board_id
    for stage in stages:
        create_new_stage(stage, db, new_board.id)

    if len(stages) > 0:
        db.commit() # Only commit a second time if we really have stages that were created


    return new_board

@router.put("/{id}", response_model=BoardDataReturn)
def update_board(id: UUID4, client_data: BoardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(id, db, current_user)

    board_dict = client_data.model_dump()
    stages: List[StageUpdate] = board_dict.pop("stages")

    board_query.update(board_dict, synchronize_session=False)
    
    update_stages(stages, db, id)

    db.commit()
    
    return board_query.first()

@router.delete("/{id}")
def delete_board(id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(id, db, current_user)

    for stage in board.stages:
        delete_stage(stage.__dict__, db)

    board_query.delete()

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)



def get_tasks_by_stage(db: Session, stage_id: UUID4):
    tasks = db.query(Task).filter(Task.stage_id == stage_id).all()

    return tasks