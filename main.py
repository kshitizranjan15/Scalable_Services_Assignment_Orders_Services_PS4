from fastapi import FastAPI, HTTPException, Query
from db_utils import get_connection
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uvicorn

app = FastAPI(title="ECI Orders API", version="1.0")

# ----------- MODELS ------------

class OrderItem(BaseModel):
    product_id: int
    order_id: Optional[int] = None
    sku: str
    quantity: int
    unit_price: float

class Order(BaseModel):
    order_id: Optional[int] = None
    customer_id: int
    order_total: float
    order_status: str = "PENDING"
    payment_status: str = "UNPAID"
    created_at: Optional[datetime] = None
    items: list[OrderItem]

# ----------- ORDER ENDPOINTS ------------

@app.get("/orders")
def get_orders(limit: int = Query(default=10, gt=0)):
    conn = get_connection("order_db")
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Orders LIMIT %s", (limit,))
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.post("/orders")
def add_order(order: Order):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Orders (order_id, customer_id, order_status, payment_status, order_total, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (order.order_id, order.customer_id, order.order_status,
              order.payment_status, order.order_total, order.created_at))
        
        for item in order.items:
            cur.execute("""
                INSERT INTO Order_Items (order_item_id, order_id, product_id, sku, quantity, unit_price)
                VALUES (NULL, %s, %s, %s, %s, %s)
            """, (item.order_id, item.product_id, item.sku, item.quantity, item.unit_price))
        
        conn.commit()
        return {"message": "✅ Order inserted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
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
        
        cur.execute("SELECT * FROM Order_Items WHERE order_id = %s", (order_id,))
        order["items"] = cur.fetchall()
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.put("/orders/{order_id}")
def update_order(order_id: int, updated_order: Order):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Orders 
            SET customer_id=%s, order_status=%s, payment_status=%s, order_total=%s 
            WHERE order_id=%s
        """, (updated_order.customer_id, updated_order.order_status, updated_order.payment_status,
              updated_order.order_total, order_id))
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")

        return {"message": "✅ Order updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.delete("/orders/{order_id}")
def delete_order(order_id: int):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Order_Items WHERE order_id = %s", (order_id,))
        cur.execute("DELETE FROM Orders WHERE order_id = %s", (order_id,))
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")

        return {"message": f"🗑️ Order {order_id} deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ----------- ORDER ITEMS ENDPOINTS ------------

@app.get("/order_items")
def get_order_items(limit: int = Query(default=10, gt=0)):
    conn = get_connection("order_db")
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Order_Items LIMIT %s", (limit,))
        return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.get("/order_items/{order_item_id}")
def get_order_item_by_id(order_item_id: int):
    conn = get_connection("order_db")
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM Order_Items WHERE order_item_id = %s", (order_item_id,))
        order_item = cur.fetchone()
        if not order_item:
            raise HTTPException(status_code=404, detail="Order item not found")
        return order_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.post("/order_items")
def add_order_item(order_item: OrderItem):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Order_Items (order_item_id, order_id, product_id, sku, quantity, unit_price)
            VALUES (NULL, %s, %s, %s, %s, %s)
        """, (order_item.order_id, order_item.product_id, order_item.sku, order_item.quantity, order_item.unit_price))
        conn.commit()
        return {"message": "✅ Order item inserted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.put("/order_items/{order_item_id}")
def update_order_item(order_item_id: int, updated_order_item: OrderItem):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Order_Items 
            SET order_id=%s, product_id=%s, sku=%s, quantity=%s, unit_price=%s 
            WHERE order_item_id=%s
        """, (
            updated_order_item.order_id,
            updated_order_item.product_id,
            updated_order_item.sku,
            updated_order_item.quantity,
            updated_order_item.unit_price,
            order_item_id
        ))
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order item not found")

        return {"message": "✅ Order item updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@app.delete("/order_items/{order_item_id}")
def delete_order_item(order_item_id: int):
    conn = get_connection("order_db")
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Order_Items WHERE order_item_id = %s", (order_item_id,))
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order item not found")

        return {"message": f"🗑️ Order item {order_item_id} deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    # Bind to 0.0.0.0 so the server is reachable from Docker containers / host mappings
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)