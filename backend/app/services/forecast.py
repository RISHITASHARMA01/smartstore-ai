from datetime import datetime, timezone, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from ..models import Product, StockHistory


def get_demand_forecast(db: Session, product_id: int):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active == True)
        .first()
    )
    if not product:
        return None

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    records = (
        db.query(StockHistory)
        .filter(
            StockHistory.product_id == product_id,
            StockHistory.change_type == "sale",
            StockHistory.recorded_at >= thirty_days_ago,
        )
        .all()
    )

    daily_sales = defaultdict(int)
    for r in records:
        if r.recorded_at:
            day = r.recorded_at.date()
            daily_sales[day] += abs(r.change_qty)

    # Build 30-day series (missing days = 0)
    all_quantities = []
    for i in range(30, 0, -1):
        d = (now - timedelta(days=i)).date()
        all_quantities.append(daily_sales.get(d, 0))

    today = now.date()

    if not any(q > 0 for q in all_quantities):
        # No sales history — flat forecast based on reorder threshold
        daily_avg = product.reorder_threshold / 7
        return {
            "product_id": product.id,
            "product_name": product.name,
            "forecast": [
                {
                    "date": str(today + timedelta(days=i)),
                    "predicted_qty": round(daily_avg, 1),
                }
                for i in range(1, 8)
            ],
        }

    # Exponential smoothing (alpha = 0.3)
    alpha = 0.3
    smoothed = float(all_quantities[0])
    for qty in all_quantities[1:]:
        smoothed = alpha * qty + (1 - alpha) * smoothed

    return {
        "product_id": product.id,
        "product_name": product.name,
        "forecast": [
            {
                "date": str(today + timedelta(days=i)),
                "predicted_qty": round(smoothed, 1),
            }
            for i in range(1, 8)
        ],
    }
