from fastapi import FastAPI
from controllers.IndiStockController import router as indi_stock_router
from controllers.StockTalkController import router as stock_talk_router
from controllers.FinancialStatementController import router as financial_statement_router
from database import engineconn, Stock

import sys
import os

engine = engineconn()
session = engine.sessionmaker()

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_directory, "controllers"))
sys.path.append(os.path.join(current_directory, "services"))

app = FastAPI()

app.include_router(indi_stock_router, prefix="/indi-stock", tags=["indi-stock"])
app.include_router(stock_talk_router, prefix="/stock-talk", tags=["stock-talk"])
app.include_router(financial_statement_router, prefix="/financial-statement", tags=["financial-statement"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.get("/first")
async def first_get():
    example = session.query(Stock).filter(Stock.name == 'NAVER').all()
    return example

