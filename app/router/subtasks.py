from typing import List

from pydantic import UUID4
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.schemas import SubtaskCreate, SubtaskUpdate
from app.models import Subtask
from app.utils.validation import validate_uuid


router = APIRouter(prefix="/subtasks", tags=["Subtasks"])


@router.put("/{id}")
def toggle_subtask_complete(id: UUID4, db: Session = Depends(get_db)):

    subtask_query = db.query(Subtask).filter(Subtask.id == id)
    subtask = subtask_query.first()

    subtask_query.update({'is_completed': not subtask.is_completed})

    db.commit()

    return subtask


def update_subtasks(subtasks: List[SubtaskCreate | SubtaskUpdate], db: Session, task_id):
    for subtask in subtasks:
        create_new_subtask(subtask, db, task_id)
        validate_subtask_id(subtask)
        process_marked_for_deletion(subtask, db)
        update_subtask(subtask, db)


def create_new_subtask(subtask: SubtaskCreate | SubtaskUpdate, db: Session, task_id: UUID4):
    print(subtask)
    if subtask.get('is_new'):
        new_subtask = Subtask(task_id=task_id, title=subtask['title'],
                              index=subtask['index'], is_completed=subtask['is_completed'])
        db.add(new_subtask)


def validate_subtask_id(subtask: SubtaskUpdate):
    if subtask.get('id') and not validate_uuid(subtask.get('id')):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid ID for subtask with title {subtask.title}")


def process_marked_for_deletion(subtask: SubtaskUpdate, db: Session):
    if subtask.get('markedForDeletion'):
        db.query(Subtask).filter(Subtask.id == subtask['id']).delete()


def update_subtask(subtask: SubtaskUpdate, db: Session):
    if subtask.get('id') and not subtask.get('markedForDeletion'):
        updated_subtask_data = {
            'title': subtask['title'],
            'index': subtask['index'],
            'is_completed': subtask['is_completed']
        }

        db.query(Subtask).filter(Subtask.id ==
                                 subtask['id']).update(updated_subtask_data)


def delete_subtask(subtask: Subtask, db: Session):
    dict = subtask.__dict__
    dict.update({'markedForDeletion': True})
    process_marked_for_deletion(dict, db)
