from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired
import uuid


app = FastAPI()

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    name: str
    user_id: str

users = {
    "user123": {
        "password": "password123",
        "name": "Иван Петров",
        "user_id": str(uuid.uuid4())
    },
    "alice": {
        "password": "alice123",
        "name": "Алиса Иванова",
        "user_id": str(uuid.uuid4())
    }
}

SECRET_KEY = "mysecretkey"
serializer = URLSafeTimedSerializer(SECRET_KEY)

@app.post("/login")
async def login(login_data: UserLogin, response: Response):
    user = users.get(login_data.username)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = user["user_id"]
    token = serializer.dumps(user_id)
    response.set_cookie(key="session_token",value=token,httponly=True,max_age=300)
    return {
        "message": "Login successful",
        "user_id": user_id
    }

@app.get("/profile")
async def get_profile(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: No session token provided")
    user_profile = None
    username = None
    try:
        user_id = serializer.loads(token,max_age=300)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Unauthorized: Session token expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid session token signature")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid session token")
    for name, data in users.items():
        if data["user_id"] == user_id:
            user_profile = data
            username = name
            break
    if not user_profile:
        raise HTTPException(status_code=401, detail="Unauthorized: User not found")
    return UserProfile(
        username=username,
        name=user_profile["name"],
        user_id=user_id
    )

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="session_token")
    return {"message": "Logout successful"}