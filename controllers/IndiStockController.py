from fastapi import APIRouter
import services.IndiStockService as IndiStockService
router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello World"}


# 실시간 현재가(장 중에만 가능해서 내일 테스트)
@router.get("/{stockCodke}/price")
async def getRealTimeStockPrice(stockCode: str):
    priceInfo = IndiStockService.indi_app_instance.real_stock_price(stockCode)
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

# 현물 마스터, 현물 종목상태정보(vi), 현물 종목 정보 조회
@router.get("/{stockCode}/info")
async def getStockinfo(stockCode: str):
    stock_info = await IndiStockService.indi_app_instance.stock_info(stockCode)
    return {'stock_info': stock_info}

# 시장 조치 실시간
@router.get("/market-actions")
async def getStockScore():
    actions = IndiStockService.indi_app_instance.market_actions()
    return {'actions': actions}
# 체결 강도 분차트, 일차트
