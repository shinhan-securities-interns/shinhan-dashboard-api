import asyncio

import anyio
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks

import database.RedisDriver
from controllers.IndiStockController import router as indi_stock_router
from controllers.FinancialStatementController import router as financial_statement_router

import services.StockTalkService as StockTalkService

#from database import engineconn, Stock
import httpx;

import sys
import os
import pandas as pd

#engine = engineconn()
#session = engine.sessionmaker()

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_directory, "controllers"))
sys.path.append(os.path.join(current_directory, "services"))

app = FastAPI()

app.include_router(indi_stock_router, prefix="/indi-stock", tags=["indi-stock"])
app.include_router(financial_statement_router, prefix="/financial-statement", tags=["financial-statement"])


def get_app():
    return app

@app.on_event("startup")
async def startup_event():
    print("startup_event")
    app.state.redis0 = database.RedisDriver.RedisDriver("localhost:6322/0")
    app.state.redis1 = database.RedisDriver.RedisDriver("localhost:6322/1")
    app.state.redis2 = database.RedisDriver.RedisDriver("localhost:6322/2")
    app.state.redis_stocktalk_contents = database.RedisDriver.RedisDriver("localhost:6322/3")
    app.state.http_client = httpx.AsyncClient()

    await save_csv_to_redis()

async def save_csv_to_redis():
    # 열 이름을 직접 명시
    column_names = ['종목코드', '종목명']
    df = pd.read_csv('./단축코드_한글종목약명.csv', names=column_names)

    for index, row in df.iterrows():
        # 종목 코드와 종목명을 결합하여 key 생성
        key = f"{row['종목코드']}_{row['종목명']}"

        # Redis에 key-value 쌍 저장
        if index < 1000:
            await app.state.redis0.setKey(key, 1, 60 * 60 * 24 * 30)
        elif 1000 <= index < 2000:
            await app.state.redis1.setKey(key, 1, 60 * 60 * 24 * 30)
        else:
            await app.state.redis2.setKey(key, 1, 60 * 60 * 24 * 30)


@app.get("/stock-talk/{code}")
async def crawl_stock_talk(code: str, background_tasks: BackgroundTasks):

    result = await StockTalkService.getCrawlStockTalkBoard(code)
    response_data = {"board": result}
    print(response_data)

    idx = 0

    inputQueue = asyncio.Queue()

    async def process_item(item, idx):
        stockTalkPostUrl = item["href"]
        print("stockTalkPostUrl : " + stockTalkPostUrl)

        # 기존 code_idx_* 키 레디스에서 삭제 @TODO
        # 0부터 19까지 삭제
        for i in range(20):
            await app.state.redis_stocktalk_contents.deleteKeyWithPrefix(code + "_" + str(i))

        async with httpx.AsyncClient() as client:
            response = await client.get(stockTalkPostUrl)

            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                body = soup.find('div', {'id': 'body'})
                content = body.text
                print(content)

                # 캐시 저장
                await inputQueue.put((idx, code + "_" + str(idx) + "_" + content))

            except UnicodeDecodeError as e:
                print(f"UnicodeDecodeError: {e}")

    async with anyio.create_task_group() as tg:
        for idx, item in enumerate(result):
            tg.start_soon(process_item, item, idx)

    await cacheToRedis(inputQueue)

    return response_data

async def cacheToRedis(inputQueue):
    results = []

    while not inputQueue.empty():
        idx, item = await inputQueue.get()
        results.append((idx, item))

    results.sort(key=lambda x: x[0])

    for _, item in results:
        await app.state.redis_stocktalk_contents.setKey(item, 0, 60 * 60 * 24)


@app.get("/stock-talk/{code}/contents/{index}")
async def getContentsFromRedis(code: str, index: str):
    if(await app.state.redis_stocktalk_contents.getContentsWithCodeAndIndex(code + "_" + index) == None):

        result = await StockTalkService.getCrawlStockTalkBoard(code)
        response_data = {"board": result}
        print(response_data)

        idx = 0

        inputQueue = asyncio.Queue()

        async def process_item(item, idx):
            stockTalkPostUrl = item["href"]
            print("stockTalkPostUrl : " + stockTalkPostUrl)

            # 기존 code_idx_* 키 레디스에서 삭제 @TODO
            # 0부터 19까지 삭제
            for i in range(20):
                await app.state.redis_stocktalk_contents.deleteKeyWithPrefix(code + "_" + str(i))

            async with httpx.AsyncClient() as client:
                response = await client.get(stockTalkPostUrl)

                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    body = soup.find('div', {'id': 'body'})
                    content = body.text
                    print(content)

                    # 캐시 저장
                    await inputQueue.put((idx, code + "_" + str(idx) + "_" + content))

                except UnicodeDecodeError as e:
                    print(f"UnicodeDecodeError: {e}")

        async with anyio.create_task_group() as tg:
            for idx, item in enumerate(result):
                tg.start_soon(process_item, item, idx)

        await cacheToRedis(inputQueue)

    contents = await app.state.redis_stocktalk_contents.getContentsWithCodeAndIndex(code + "_" + index)

    return contents