from fastapi import FastAPI, Header, HTTPException
from typing import Optional

app = FastAPI()

def validate_accept_language(accept_language: str) -> bool:
    parts = accept_language.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            return False
        if ';q=' in part:
            lang_part, q_part = part.split(';q=', 1)
            if not lang_part.strip():
                return False
            try:
                q_value = float(q_part)
                if not (0 <= q_value <= 1):
                    return False
            except ValueError:
                return False
        else:
            if not part:
                return False
    return True

@app.get("/headers")
async def get_headers(
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
    accept_language: Optional[str] = Header(None, alias="Accept-Language")
):
    if not user_agent:
        raise HTTPException(status_code=400,detail="Missing User-Agent")
    if not accept_language:
        raise HTTPException(status_code=400,detail="Missing Accept-Language")
    if not validate_accept_language(accept_language):
        raise HTTPException(status_code=400, detail="Invalid Accept-Language header format")
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }