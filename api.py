import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

app = FastAPI(title="BarghApp Plus API")

API_KEY = os.getenv("MY_INTERNAL_API_KEY", "your-secret-api-key-here")
print(f"-----> Loded API KEY: {API_KEY} <-----") # این خط را برای تست اضافه کنید
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key_header




DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "database _name")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}?charset=utf8mb4"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
except Exception as e:
    print(f"Error connecting to DB: {e}")


@app.get("/api/barghapp_plus")
def get_plus_data(
        limit: int = Query(20, ge=1, le=1000),
        last_id: int = Query(0, ge=0),  # پارامتر جدید برای دریافت از یک آی‌دی به بعد
        api_key: str = Depends(verify_api_key)
):
    """
    Fetches data from the barghapp_plus table starting from a specific ID (Incremental Fetching).
    """
    try:
        with engine.connect() as conn:
            # تغییر کوئری: فقط رکوردهایی که آی‌دی آن‌ها بزرگتر از last_id است را صعودی بیاور
            query = text("""
                SELECT * FROM `database_tabel` 
                WHERE `id` > :last_id 
                ORDER BY `id` ASC 
                LIMIT :limit
            """)
            result = conn.execute(query, {"limit": limit, "last_id": last_id})

            # تبدیل ردیف‌ها به لیست دکشنری
            rows = [dict(row) for row in result.mappings()]

            return {
                "success": True,
                "table": "database_tabel",
                "count": len(rows),
                "data": rows
            }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
