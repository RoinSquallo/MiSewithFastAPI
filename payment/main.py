from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
import requests, time


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

# This should be a different database
redis = get_redis_connection(
    host="redis-19701.c290.ap-northeast-1-2.ec2.cloud.redislabs.com",
    port=19701,
    password="8fuTjrRi4MUiy8xmPUH4Ki7hSPo0g5u8",
    decode_responses=True
)

class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str #pending, completed, refunded

    class Meta:
        database = redis
    

@app.get('/orders/{pk}')
def get(pk: str):
    return Order.get(pk)

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    req = requests.get('http://localhost:8000/products/%s' % body['id'])
    product = req.json()

    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending'
    )

    order.save()
    background_tasks.add_task(order_completed, order)

    return order

def order_completed(order: Order):
    print('1')
    time.sleep(5)
    print('2')
    order.status = 'completed'
    print('3')
    order.save()
    print('4')
    redis.xadd('order_completed', order.dict(),'*')
    print(order.status)