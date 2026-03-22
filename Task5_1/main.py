from fastapi import FastAPI,HTTPException, Response, Request
from pydantic import BaseModel
import uuid

app=FastAPI()
class User(BaseModel):
    username: str
    password: str

users = {
    "user123": {"password": "password123", "name": "Иван Петров"},
    "alice" : {"password": "alice123", "name" : "Алиса Петровна"}
}
sessions = {}

@app.post('/login')
async def login(login_data: User, response: Response):
    user = users.get(login_data.username)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = str(uuid.uuid4())
    sessions[token] = login_data.username
    response.set_cookie(key="session_token",value=token)
    return {"message": "Login successful"}

@app.get('/user')
async def get_user(request: Request):
    token = request.cookies.get("session_token")
    if not token or token not in sessions:
        raise HTTPException(status_code=401, detail="Unauthorized")
    username = sessions[token]
    return {
        "username": username,
        "name": users[username]["name"]
    }