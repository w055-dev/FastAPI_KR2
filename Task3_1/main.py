from fastapi import FastAPI
from pydantic import BaseModel,EmailStr
from typing import Optional

app=FastAPI()
class User(BaseModel):
    name: str 
    email: EmailStr
    age: Optional[int] = None
    is_subscribed: bool = False

@app.post('/create_user')
async def create_user(user : User):
    return user.model_dump()