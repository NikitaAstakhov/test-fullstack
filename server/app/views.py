import random
import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from databases import Database

from db.crud import insert_submission, get_history
from app.main import database
from schemas.submission import ErrorResponse, SuccessResponse, HistoryItem, SubmitPayload

router = APIRouter()


@router.post(
    "/submit",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 422: {}},
)
async def submit_form(
    payload: SubmitPayload,
    db: Database = Depends(lambda: database),
):
    await asyncio.sleep(random.uniform(0, 3))

    try:
        await insert_submission(
            db,
            date=payload.date,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    full_name = f"{payload.first_name} {payload.last_name}"
    count = random.randint(2, 5)
    data_list = [
        {"date": payload.date.isoformat(), "name": full_name} for _ in range(count)
    ]

    return {"success": True, "data": data_list}


@router.get(
    "/history",
    response_model=List[HistoryItem],
    responses={500: {"description": "Database error"}}
)
async def history(db: Database = Depends(lambda: database)):
    try:
        records = await get_history(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return records
