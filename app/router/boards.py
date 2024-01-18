from typing import List

from pydantic import UUID4
from app.database import get_db
from app.router.stages import create_new_stage, delete_stage, update_stages
from app.schemas import BoardCreateResponse, BoardDataReturn, BoardListReturn, BoardCreate, BoardUpdate, ContributorUpdate, StageCreate, StageUpdate, UserInfoReturn
from app.models import Task, User, Board, boards_users
from app.oauth2 import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.utils.helpers import get_index, getListDiff

from app.utils.validation import get_board_from_db


router = APIRouter(prefix="/boards", tags=["Boards"])


@router.get("/", response_model=BoardListReturn)
def get_users_boards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    # Easiest way is to simply get the user from the database since our Model holds a direct relationship to all boards that the user is owning or contributing to.
    user = db.query(User).filter(User.id == current_user.id).first()

    return {"own_boards": user.own_boards, "contributing": user.boards_contributing}


@router.get("/{id}", response_model=BoardDataReturn)
def get_board_data(id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    (board_query, board) = get_board_from_db(id, db, current_user)

    stages = board.stages
    stages.sort(key=get_index)

    return board


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BoardCreateResponse)
def create_board(board: BoardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    board_dict = board.model_dump()
    stages: List[StageCreate] = board_dict.pop('stages')
    contributors: List[UUID4] = get_new_contributors(
        board_dict.pop("contributors"))

    new_board = Board(**board_dict)

    db.add(new_board)
    db.commit()
    db.refresh(new_board)

    # After board creation we can access its ID to create the stages with the fkey board_id
    for stage in stages:
        create_new_stage(stage, db, new_board.id)

    add_contributors(contributors, db, new_board)

    if len(stages) > 0 or len(contributors) > 0:
        db.commit()  # Only commit a second time if we really have stages or contributors that were created

    return new_board


@router.put("/{id}", response_model=BoardDataReturn)
def update_board(id: UUID4, client_data: BoardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(id, db, current_user)

    is_client_owner = current_user.id == board.owner_id

    board_dict = client_data.model_dump()
    incoming_stages: List[StageUpdate] = board_dict.pop("stages")
    incoming_contributors: List[ContributorUpdate] = board_dict.pop(
        "contributors")

    removed_contributors: List[UUID4] = get_removed_contributors(
        incoming_contributors)
    new_contributors: List[UUID4] = get_new_contributors(incoming_contributors)

    board_query.update(board_dict, synchronize_session=False)

    update_stages(incoming_stages, db, id)
    if is_client_owner:
        add_contributors(new_contributors, db, board)
        remove_contributors(removed_contributors, db, board)

    db.commit()

    return board_query.first()


@router.patch("/{board_id}/owner/{owner_id}", response_model=BoardDataReturn)
def change_board_owner(board_id: UUID4, owner_id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(board_id, db, current_user)
    new_owner = db.query(User).filter(User.id == owner_id).first()

    if board.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Only the owner of this board can set a new owner.")

    board.contributors.remove(new_owner)
    board_query.update({'owner_id': owner_id})
    board.contributors.append(current_user)

    db.commit()

    return board_query.first()


@router.delete("/{id}")
def delete_board(id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    (board_query, board) = get_board_from_db(id, db, current_user)

    if not current_user.id == board.owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'Only the owner of this board can delete it!')

    for stage in board.stages:
        delete_stage(stage.__dict__, db)

    for contributor in board.contributors:
        board.contributors.remove(contributor)
    db.commit()

    board_query.delete()
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def get_tasks_by_stage(db: Session, stage_id: UUID4):
    tasks = db.query(Task).filter(Task.stage_id == stage_id).all()

    return tasks


def add_contributors(users: List[UUID4], db: Session, board: Board):
    for contributor in users:
        new_contributor = db.query(User).filter(User.id == contributor).first()
        if not new_contributor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'User with ID {contributor} not found.')
        board.contributors.append(new_contributor)


def remove_contributors(users: List[UUID4], db: Session, board: Board):
    for contributor in users:
        user = db.query(User).filter(User.id == contributor).first()
        board.contributors.remove(user)


def get_removed_contributors(contributors: ContributorUpdate):
    return [user['id'] for user in contributors if user['marked_for_deletion']]


def get_new_contributors(contributors: ContributorUpdate):
    return [user['id'] for user in contributors if user['is_new']]
