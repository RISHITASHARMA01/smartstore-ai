from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth.bypass import get_user_dependency
get_current_user = get_user_dependency()
from ..services.forecast import get_demand_forecast

router = APIRouter(
    prefix="/products",
    tags=["forecast"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{product_id}/forecast")
def forecast(product_id: int, db: Session = Depends(get_db)):
    result = get_demand_forecast(db, product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return result
