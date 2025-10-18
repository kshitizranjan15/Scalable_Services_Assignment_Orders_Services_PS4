from fastapi import FastAPI, HTTPException, Query
from db_utils import get_connection
from pydantic import BaseModel
from datetime import datetime
import uvicorn

app = FastAPI(title="ECI Orders API", version="1.0")

# ----------- ORDER SECTION ------------
class OrderItem(BaseModel):
    product_id: int
    sku: str
    quantity: int
    unit_price: float

class Order(BaseModel):
    order_id: int
    customer_id: int
    order_total: float
    order_status: str = "PENDING"
    payment_status: str = "UNPAID"
    created_at: datetime = datetime.now()
    items: list[OrderItem]


@app.get("/orders")
def get_orders(limit: int = Query(default=10, gt=0, description="Limit number of orders to fetch")):
    conn = get_connection("order_db")
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT * FROM Orders LIMIT {limit}")
        orders = cur.fetchall()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/orders")
def add_order(order: Order):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        # Insert order header
        cur.execute("""
            INSERT INTO Orders (order_id, customer_id, order_status, payment_status, order_total, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (order.order_id, order.customer_id, order.order_status,
              order.payment_status, order.order_total, order.created_at))
        
        # Insert order items
        for item in order.items:
            cur.execute("""
                INSERT INTO Order_Items (order_item_id, order_id, product_id, sku, quantity, unit_price)
                VALUES (NULL, %s, %s, %s, %s, %s)
            """, (order.order_id, item.product_id, item.sku, item.quantity, item.unit_price))
        
        conn.commit()
        return {"message": "✅ Order inserted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/orders/{order_id}")
def get_order_by_id(order_id: int):
    conn = get_connection("order_db")
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Orders WHERE order_id = %s", (order_id,))
        order = cur.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Fetch order items
        cur.execute("SELECT * FROM Order_Items WHERE order_id = %s", (order_id,))
        items = cur.fetchall()
        order["items"] = items
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
