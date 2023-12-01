from typing import List
import uuid
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Table, asc, text, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

boards_users = Table(
    "boards_users",
    Base.metadata,
    Column("board_id", ForeignKey("boards.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_email_verified: Mapped[bool] = mapped_column(nullable=False, server_default='False')
    password: Mapped[str] = mapped_column(nullable=False)

    own_boards: Mapped[List["Board"]] = relationship(back_populates="owner")
    boards_contributing: Mapped[List["Board"]] = relationship(secondary=boards_users, back_populates="contributors")

    def __repr__(self) -> str:
        return f"<User username={self.first_name} {self.last_name}>"


class Board(Base):
    __tablename__ = "boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="own_boards")
    contributors: Mapped[List["User"]] = relationship(secondary=boards_users, back_populates="boards_contributing")
    
    stages: Mapped[List["Stage"]] = relationship(order_by='asc(Stage.index)')

    def __repr__(self) -> str:
        return f"<Board title={self.title} created by {self.owner.first_name} {self.owner.last_name}>"


# Class is called "Stage" as referred to the kanban stage to avoid naming clash with 'Column' from sqlalchemy
class Stage(Base):
    __tablename__ = "stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    title: Mapped[str] = mapped_column(nullable=False)
    index: Mapped[int] = mapped_column(nullable=False)
    color: Mapped[str] = mapped_column(nullable=False)
    board_id: Mapped[str] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    tasks: Mapped[List["Task"]] = relationship(back_populates="status")

    def __repr__(self) -> str:
        return f"<Stage title={self.title} of board {self.board_id}>"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[str] = mapped_column(ForeignKey("stages.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    status: Mapped["Stage"] = relationship()
    subtasks: Mapped[List["Subtask"]] = relationship(order_by='asc(Subtask.index)')

    def __repr__(self) -> str:
        return f"<Task title={self.title} in stage {self.stage_id}>"



class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    index: Mapped[int] = mapped_column(nullable=False)
    is_completed: Mapped[bool] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"<Subtask title={self.title} status {self.is_completed}>"
