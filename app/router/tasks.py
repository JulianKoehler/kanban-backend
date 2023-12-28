from typing import List

from pydantic import UUID4
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.database import get_db
from app.router.subtasks import create_new_subtask, delete_subtask, update_subtasks
from app.schemas import SubtaskCreate, TaskCreate, TaskDeleteResponse, TaskResponse, TaskUpdate, TaskUpdateAssignedUser, TaskUpdateStage
from app.models import Stage, Task, User, Board
from app.oauth2 import get_current_user
from app.utils.helpers import get_index
from app.utils.validation import check_board_permission


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskResponse)
def create_task(client_data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    board = db.query(Board).filter(Board.id == client_data.board_id).first()
    check_board_permission(board, current_user.id)

    task = client_data.model_dump(exclude='board_id')
    subtasks = task.pop('subtasks')

    new_task = Task(**task)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # After task creation we can access its ID to create the subtasks with the fkey task_id
    subtasks_exist = len(subtasks) > 0
    if subtasks_exist:
        for subtask in subtasks:
            create_new_subtask(subtask, db, new_task.id)

        db.commit()

    return new_task


@router.put("/{id}", response_model=TaskResponse)
def update_task(id: UUID4, client_data: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    board = db.query(Board).filter(Board.id == client_data.board_id).first()
    check_board_permission(board, current_user.id)

    task_query = db.query(Task).filter(Task.id == id)
    task = task_query.first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Task with id {id} not found")

    new_task_data = client_data.model_dump(exclude=['board_id'])
    subtasks: List[SubtaskCreate] = new_task_data.pop('subtasks')

    task_query.update(new_task_data, synchronize_session=False)
    update_subtasks(subtasks, db, task.id)
    db.commit()

    return task

@router.patch("/stage/{id}",response_model=TaskResponse)
def update_stage(id: UUID4, client_data: TaskUpdateStage, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    task_query = db.query(Task).filter(Task.id == id)
    task = task_query.first()
    stage = db.query(Stage).filter(Stage.id == task.stage_id).first()
    board = db.query(Board).filter(Board.id == stage.board_id).first()

    check_board_permission(board, current_user.id)

    task_query.update({ "stage_id": client_data.new_stage_id })
    db.commit()

    return task


@router.patch("/assignment/{id}",response_model=TaskResponse)
def update_stage(id: UUID4, client_data: TaskUpdateAssignedUser, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    task_query = db.query(Task).filter(Task.id == id)
    task = task_query.first()
    stage = db.query(Stage).filter(Stage.id == task.stage_id).first()
    board = db.query(Board).filter(Board.id == stage.board_id).first()

    check_board_permission(board, current_user.id)
    check_board_permission(board, client_data.assigned_user_id)

    task_query.update({ 'assigned_user_id': client_data.assigned_user_id })
    db.commit()

    return task


@router.delete("/{id}", response_description="Task successfully deleted", response_model=TaskDeleteResponse)
def delete_task(id: UUID4, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    task_query = db.query(Task).filter(Task.id == id)
    task = task_query.first()
    stage = db.query(Stage).filter(Stage.id == task.stage_id).first()
    board = db.query(Board).filter(Board.id == stage.board_id).first()
    check_board_permission(board, current_user.id)

    for subtask in task.subtasks:
        delete_subtask(subtask, db)

    task_query.delete()

    db.commit()

    return {
        "board_id": board.id,
        "stage_id": stage.id
    }
