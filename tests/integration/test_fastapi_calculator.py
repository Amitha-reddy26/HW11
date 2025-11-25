from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class Numbers(BaseModel):
    a: float
    b: float


@router.post("/add")
def add(nums: Numbers):
    return {"result": nums.a + nums.b}


@router.post("/subtract")
def subtract(nums: Numbers):
    return {"result": nums.a - nums.b}


@router.post("/multiply")
def multiply(nums: Numbers):
    return {"result": nums.a * nums.b}


@router.post("/divide")
def divide(nums: Numbers):
    if nums.b == 0:
        return JSONResponse(
            status_code=400,
            content={"error": "Cannot divide by zero!"}
        )
    return {"result": nums.a / nums.b}
