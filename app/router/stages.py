from typing import List

from pydantic import UUID4
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db

from app.models import Board, Stage, User
from app.oauth2 import get_current_user
from app.schemas import StageCreate, StageResponse, StageUpdate
from app.utils.validation import check_board_permission, validate_uuid

router = APIRouter(prefix="/stages", tags=["Stages"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StageResponse)
def create_stage(client_data: StageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if not validate_uuid(client_data.board_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Please provide a valid UUID4 as reference to the board of this stage")

    board = db.query(Board).filter(Board.id == client_data.board_id).first()
    check_board_permission(board, current_user.id)

    new_stage = Stage(**client_data.model_dump())
    db.add(new_stage)
    db.commit()
    db.refresh(new_stage)

    return new_stage


def update_stages(stages: List[StageUpdate], db: Session, board_id):
    for stage in stages:
        create_new_stage(stage, db, board_id)
        validate_stage_id(stage)
        process_marked_for_deletion(stage, db)
        update_stage(stage, db)


def create_new_stage(stage: StageUpdate, db: Session, board_id: UUID4):
    if not stage.get('id') and not stage.get('markedForDeletion'):
        stage_data: StageCreate = {
            "title": stage['title'],
            "index": stage['index'],
            "color": stage['color'],
            "board_id": board_id
        }
        new_stage = Stage(**stage_data)
        db.add(new_stage)
        return new_stage


def validate_stage_id(stage: StageUpdate):
    if stage.get('id') and not validate_uuid(stage.get('id')):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid ID for stage with title {stage.title}")


def process_marked_for_deletion(stage: StageUpdate, db: Session):
    if stage.get('markedForDeletion'):
        db.query(Stage).filter(Stage.id == stage['id']).delete()


def update_stage(stage: StageUpdate, db: Session):
    if stage.get('id') and not stage.get('markedForDeletion'):
        updated_stage_data = {
            'title': stage['title'],
            'index': stage['index'],
            'color': stage['color']
        }

        db.query(Stage).filter(
            Stage.id == stage['id']).update(updated_stage_data)


def delete_stage(stage: StageUpdate, db: Session):
    stage.update({'markedForDeletion': True})
    process_marked_for_deletion(stage, db)
