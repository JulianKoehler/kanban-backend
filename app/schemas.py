from datetime import datetime
from typing import List, Optional
from pydantic import UUID4, BaseModel, EmailStr


class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    password: str


class UserReturn(BaseModel):
    id: UUID4
    first_name: str
    last_name: Optional[str]
    email: EmailStr


class UserInfoReturn(UserReturn):
    created_at: datetime
    is_email_verified: bool


class UserPasswordResetRequest(BaseModel):
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class NewUserPassword(Token):
    password: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class SubtaskCreate(BaseModel):
    title: str
    index: int
    is_completed: bool


class SubtaskUpdate(SubtaskCreate):
    id: UUID4 | str
    markedForDeletion: Optional[bool] = False
    is_new: Optional[bool] = False


class SubtaskResponse(SubtaskUpdate):
    pass


class TaskBase(BaseModel):
    title: str
    description: str


class TaskCreate(TaskBase):
    board_id: str
    stage_id: str
    subtasks: List[SubtaskCreate]


class TaskUpdate(TaskCreate):
    subtasks: List[SubtaskUpdate]


class TaskUpdateStage(BaseModel):
    new_stage_id: UUID4


class Status(BaseModel):
    id: UUID4
    title: str


class TaskResponse(TaskBase):
    id: UUID4
    status: Status
    subtasks: List[SubtaskResponse]


# Used in the frontend to perform a pessimistic update.
# Board and stage id needed to traverse the data structure.
class TaskDeleteResponse(BaseModel):
    board_id: UUID4
    stage_id: UUID4


class StageBase(BaseModel):
    title: str
    index: int
    color: str


class StageCreate(StageBase):
    board_id: Optional[str] = None


class StageUpdate(StageCreate):
    id: str
    markedForDeletion: Optional[bool] = False


class StageResponse(StageBase):
    id: UUID4
    tasks: List[TaskResponse]


class BoardBase(BaseModel):
    title: str


class BoardListItem(BoardBase):
    id: UUID4
    created_at: datetime


class BoardCreate(BoardBase):
    stages: List[StageCreate]


class BoardUpdate(BoardBase):
    stages: List[StageUpdate | StageCreate]


class BoardCreateResponse(BoardListItem):
    stages: List[StageResponse]
    

class BoardListReturn(BaseModel):
    own_boards: List[BoardListItem]
    contributing: List[BoardListItem]


class BoardDataReturn(BoardBase):
    id: UUID4
    stages: List[StageResponse]


class StageMigration(StageCreate):
    tasks: List[TaskCreate]

class BoardMigration(BoardBase):
    user_id: UUID4
    stages: List[StageMigration]