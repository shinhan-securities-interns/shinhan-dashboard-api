from fastapi import FastAPI
from PyQt5.QtWidgets import QApplication, QMainWindow
import threading
import uvicorn
from controllers.IndiStockController import router as indi_stock_router
from controllers.StockTalkController import router as stock_talk_router
from controllers.FinancialStatementController import router as financial_statement_router
from services.IndiStockService import run_indi_app

import sys

import os

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



def run_fastapi_server():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)


if __name__ == "__main__":
    indi_thread = threading.Thread(target=run_indi_app)
    indi_thread.start()

    server_thread = threading.Thread(target=run_fastapi_server)
    server_thread.start()