from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import users, auth, boards, stages, tasks, subtasks


app = FastAPI()

origins = ['https://kanban-board-jet.vercel.app']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(stages.router)
app.include_router(tasks.router)
app.include_router(subtasks.router)


@app.get("/")
async def root():
    return {"message": "API is up and running"}
