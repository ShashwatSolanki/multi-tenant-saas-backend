from fastapi import FastAPI
from sqlalchemy import text
from app.db.base import engine

app = FastAPI()



@app.get("/db-test")
async def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"result": result.scalar()}