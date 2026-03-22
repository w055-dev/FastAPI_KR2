from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import uuid
from datetime import datetime

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
SESSION_TIME = 300 
THREE_MINUTES = 180

def create_session_token(user_id: str, timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = int(datetime.now().timestamp())
    token_data = f"{user_id}|{timestamp}"
    return serializer.dumps(token_data)
def verify_user_id(token: str, check_expiration: bool = True) -> tuple:
    try:
        if check_expiration:
            token_data = serializer.loads(token, max_age=SESSION_TIME)
        else:
            token_data = serializer.loads(token)
        parts = token_data.split('|')
        if len(parts) != 2:
            return None, None
        user_id, timestamp_str = parts
        timestamp = int(timestamp_str)
        return user_id, timestamp
    except (BadSignature, SignatureExpired, ValueError, AttributeError):
        return None, None

@app.post("/login")
async def login(login_data: UserLogin, response: Response):
    user = users.get(login_data.username)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_id = user["user_id"]
    current_timestamp = int(datetime.now().timestamp())
    token = create_session_token(user_id, current_timestamp)
    response.set_cookie(key="session_token",value=token,httponly=True,max_age=SESSION_TIME,secure=False)
    return {
        "message": "Login successful",
        "user_id": user_id
    }

@app.get("/profile")
async def get_profile(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: No session token provided")
    user_id, last_activity_timestamp = verify_user_id(token, check_expiration=False)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    current_time = datetime.now()
    last_activity = datetime.fromtimestamp(last_activity_timestamp)
    time_passed = int((current_time - last_activity).total_seconds())
    if time_passed > SESSION_TIME:
        raise HTTPException(status_code=401, detail="Session expired")
    elif time_passed >= THREE_MINUTES and time_passed < SESSION_TIME:
        new_timestamp = int(datetime.now().timestamp())
        new_token = create_session_token(user_id, new_timestamp)
        response.set_cookie(key="session_token",value=new_token,httponly=True,max_age=SESSION_TIME,secure=False)
    user_profile = None
    username = None
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