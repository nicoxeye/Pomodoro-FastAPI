from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta


app = FastAPI()


class Task(BaseModel):
    id: str = Field(default_factory= lambda: str(uuid.uuid4()))
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field("To Do")

class PomodoroSession(BaseModel):
    taskid: str
    start_time: datetime
    end_time: datetime
    completed: bool


tasks: List[Task] = []
pomodoro_timers: List[PomodoroSession] = []
pomodoro_sessions: List[PomodoroSession] = []

@app.post("/tasks")
def create_task(task: Task):
    allowed_statuses = ["To Do", "Doing", "Done"]

    for existing_task in tasks:
        if existing_task.title == task.title:
            raise HTTPException(status_code=400, detail="Title has to be unique:P")
    
    if task.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed_statuses)}")

    tasks.append(task)
    return task


@app.get("/tasks")
def get_tasks(filter_status: str = "None"):
    filtered_tasks = []
    for task in tasks:
        if task.status == filter_status:
            filtered_tasks.append(task)
        elif filter_status == "None":
            return tasks
    return filtered_tasks


@app.get("/tasks/{task_id}")
def task_info(task_id: str = "0"):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Given ID does not exist.")


@app.put("/tasks/{task_id}")
def update_task(task_id: str, title:str, description:str, status:str):
    allowed_statuses = ["To Do", "Doing", "Done"]
    for task in tasks:
        if task.id == task_id:
            if status not in allowed_statuses:
                raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed_statuses)}")
            task.status = status
            task.title = title
            task.description = description
            return task
    raise HTTPException(status_code=404, detail="Given ID does not exist.")


@app.delete("/tasks/{task_id}")
def delete_task(task_id:str):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return f"Successfully deleted task {task_id}"
    raise HTTPException(status_code=404, detail="Given ID does not exist.")


@app.post("/pomodoro")
def create_pomodoro_timer(task_id:str, duration:int = 25):
    for pomodoro in pomodoro_timers:
        if pomodoro.taskid == task_id:
            raise HTTPException(status_code=400, detail="Task already has an active Pomodoro timer")
    for task in tasks:
        if task.id == task_id:
            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=duration)
            session = PomodoroSession(taskid=task_id, start_time=start_time, end_time=end_time, completed=False)
            pomodoro_sessions.append(session)
            pomodoro_timers.append(session)
            return session
    raise HTTPException(status_code=404, detail="Given ID does not exist.")


@app.post("/pomodoro/{task_id}/stop")
def stop_pomodoro_timer(task_id:str):
    for pomodoro in pomodoro_timers:
        if pomodoro.taskid == task_id:
            pomodoro_timers.remove(pomodoro)

    for pomodoro in pomodoro_sessions:
        if pomodoro.taskid == task_id:
            pomodoro.completed = True
            return "Successfully stopped pomodoro session."
    raise HTTPException(status_code=404, detail="No Timer of such ID found.")


@app.get("/pomodoro/stats")
def get_pomodoro_stats():
    completed_sessions = []
    stats = {}
    for session in pomodoro_sessions:
        if session.completed:
            completed_sessions.append(session)

    for session in completed_sessions:
        if session.taskid in stats:
            stats[session.taskiid] += 1
        else:
            stats[session.taskid] = 1
    
    return {"completed_sessions": stats}