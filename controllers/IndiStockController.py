from fastapi import APIRouter
from fastapi import FastAPI, BackgroundTasks, WebSocket, Request
from starlette.websockets import WebSocketDisconnect, WebSocketState
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio

import services.IndiStockService as IndiStockService

router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.connections = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

# WebSocketManager 인스턴스 생성
websocket_manager = WebSocketManager()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# WebSocket 연결을 테스트할 수 있는 웹페이지
@router.get("/client", response_class=HTMLResponse)
async def client(request: Request):
    return templates.TemplateResponse("client.html", {"request": request})

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        print(f"client connected: {websocket.client}")
        await websocket.send_text(f"Welcome client: {websocket.client}")
        while True:
            data = await websocket.receive_text()
            print(f"message received: {data} from: {websocket.client}")
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print(f"client disconnected: {websocket.client}")

@router.get("/")
async def root():
    return {"message": "Hello World"}

# 백그라운드 작업으로 주기적인 확인 등록
@router.get("/check_real_time_price/{stockCode}")
async def check_real_time_price(stockCode: str, background_tasks: BackgroundTasks):
    # 백그라운드 작업으로 주기적인 확인 등록
    background_tasks.add_task(check_real_time_stock_price, stockCode)
    return {"message": "Background task scheduled for real-time stock price checking."}

async def check_real_time_stock_price(stock_code: str):
    while True:
        price_info = await IndiStockService.indi_app_instance.real_stock_price(stock_code)

        if websocket_manager.connections:
            # Use the first (and only) websocket connection
            websocket = websocket_manager.connections.pop()
            await websocket_manager.send_message({'priceInfo': price_info}, websocket)
            # Add the websocket back to the set for future use
            websocket_manager.connections.add(websocket)

        await asyncio.sleep(1)


# 장 종료 후 현재가
@router.get("/{stockCodke}/price")
async def getRealTimeStockPrice(stockCode: str):
    priceInfo = await IndiStockService.indi_app_instance.stock_price(stockCode)
    return {'priceInfo': priceInfo}

# 종목 점수 조회
@router.get("/{stockCode}/score")
async def getStockScore(stockCode: str):
    score = await IndiStockService.indi_app_instance.stock_score(stockCode)
    return {'score': score}

# 현물 분/일/주/월 데이터
@router.get("/{stockCode}/charts/{chartType}")
async def getStockChart(stockCode: str, chartType: str):
    chartData = await IndiStockService.indi_app_instance.chart_data(stockCode, chartType)
    return {'chartData': chartData}


# 시장 조치 실시간
@router.get("/market-actions")
async def getStockScore():
    actions = IndiStockService.indi_app_instance.market_actions()
    return {'actions': actions}
# 체결 강도 분차트, 일차트
