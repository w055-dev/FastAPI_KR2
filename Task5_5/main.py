from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

app = FastAPI()

class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    @field_validator('accept_language')
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Accept-Language header cannot be empty")
        parts = v.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                raise ValueError("Invalid Accept-Language format: empty part found")
            if ';q=' in part:
                lang_part, q_part = part.split(';q=', 1)
                if not lang_part.strip():
                    raise ValueError("Invalid Accept-Language format: empty language tag")
                try:
                    q_value = float(q_part)
                    if not (0 <= q_value <= 1):
                        raise ValueError(f"Invalid q-value: {q_value}. Must be between 0 and 1")
                except ValueError:
                    raise ValueError(f"Invalid q-value format: {q_part}")
            else:
                if not part:
                    raise ValueError("Invalid Accept-Language format: empty language tag")
        return v
    class Config:
        populate_by_name = True


@app.get("/headers")
async def get_headers(headers: CommonHeaders = Header()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }


@app.get("/info")
async def get_info(headers: CommonHeaders = Header()):
    server_time = datetime.now().isoformat()
    response = JSONResponse(
        content={
            "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
            "headers": {
                "User-Agent": headers.user_agent,
                "Accept-Language": headers.accept_language
            }
        }
    )
    response.headers["X-Server-Time"] = server_time
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )