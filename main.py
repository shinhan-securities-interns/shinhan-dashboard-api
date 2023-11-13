import asyncio
import logging

import anyio
from bs4 import BeautifulSoup
from fastapi import FastAPI
from controllers.IndiStockController import router as indi_stock_router
from controllers.FinancialStatementController import router as financial_statement_router
from fastapi import BackgroundTasks

import services.StockTalkService as StockTalkService
import utils.CrawlDataFromNaverFinance as crawl

#from database import engineconn, Stock
import httpx;
import json;
from aioredis import Redis

import sys
import os
import pandas as pd
import io

#engine = engineconn()
#session = engine.sessionmaker()

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_directory, "controllers"))
sys.path.append(os.path.join(current_directory, "services"))

app = FastAPI()

app.include_router(indi_stock_router, prefix="/indi-stock", tags=["indi-stock"])
app.include_router(financial_statement_router, prefix="/financial-statement", tags=["financial-statement"])


class RedisStockTalkDependency:
    def __init__(self, redis_stocktalk_contents, http_client):
        self.redis_stocktalk_contents = redis_stocktalk_contents
        self.http_client = http_client

def save_csv_to_redis():
    # 열 이름을 직접 명시
    column_names = ['종목코드', '종목명']
    df = pd.read_csv('./단축코드_한글종목약명.csv', names=column_names)

    for index, row in df.iterrows():
        # 종목 코드와 종목명을 결합하여 key 생성
        key = f"{row['종목코드']}_{row['종목명']}"

        # Redis에 key-value 쌍 저장
        if index < 1000:
            app.state.redis0.set(key, 1)
        elif 1000 <= index < 2000:
            app.state.redis1.set(key, 1)
        else:
            app.state.redis2.set(key, 1)


@app.on_event("startup")
async def startup_event():

    print("startup_event")
    app.state.redis0 = Redis(host="localhost", port=6322, db=0, decode_responses=True)
    app.state.redis1 = Redis(host="localhost", port=6322, db=1, decode_responses=True)
    app.state.redis2 = Redis(host="localhost", port=6322, db=2, decode_responses=True)

    app.state.redis_stocktalk_contents = Redis(host="localhost", port=6322, db=3, decode_responses=True)

    app.state.http_client = httpx.AsyncClient()

    save_csv_to_redis()


@app.on_event("shutdown")
async def shutdown_event():
    print("shutdown_event")
    await app.state.redis0.close()
    await app.state.redis1.close()
    await app.state.redis2.close()
    await app.state.redis_stocktalk_contents.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

async def delete_keys_with_prefix(redis: Redis, prefix: str):
    print("delete_keys_with_prefix")
    cursor = "0"
    while cursor != 0:
        cursor, keys = await redis.scan(cursor, match=f"{prefix}*", count=100)
        if keys:
            print(f"Deleting keys: {keys}")
            await redis.delete(*keys)

@app.get("/stock-talk/{code}")
async def crawl_stock_talk(code: str, background_tasks: BackgroundTasks):

    result = await StockTalkService.getCrawlStockTalkBoard(code)
    response_data = {"board": result}
    print(response_data)

    idx = 0

    async def process_item(item):
        nonlocal idx
        stockTalkPostUrl = item["href"]
        print("stockTalkPostUrl : " + stockTalkPostUrl)

        # 기존 code_idx_* 키 레디스에서 삭제
        await delete_keys_with_prefix(app.state.redis_stocktalk_contents, code)

        async with httpx.AsyncClient() as client:
            response = await client.get(stockTalkPostUrl)
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                body = soup.find('div', {'id': 'body'})
                content = body.text

                # 캐시 저장
                await cacheToRedis(code, str(content), idx)
                idx += 1

            except UnicodeDecodeError as e:
                print(f"UnicodeDecodeError: {e}")

    async with anyio.create_task_group() as tg:
        for item in result:
            tg.start_soon(process_item, item)

    return response_data

async def cacheToRedis(code, content, idx):
    print(content)
    idx = str(idx)
    redis_key = f"{code}" + "_" + f"{idx}" + "_" + f"{content}"
    app.state.redis_stocktalk_contents.set(redis_key, "true")
    app.state.redis_stocktalk_contents.expire(redis_key, 60 * 60 * 24)


