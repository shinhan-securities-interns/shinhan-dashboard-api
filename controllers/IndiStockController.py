from fastapi import APIRouter
import services.IndiStockService as IndiStockService
router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello World"}


# 실시간 현재가
# 시장 조치 실시간
# 종목 점수 조회
# 현물

@router.get("/indi/stock/news")
async def news_list():
    print("call news list")
    IndiStockService.indi_app_instance.search_stock_news()
    print("called news list")

    return {"message": "success get stock newas"}


@router.get("/indi/stock/info")
async def info():
    print("call info")
    IndiStockService.indi_app_instance.pushButton_search_stock_info()
    print("called info")

    return {"message": "success get stock info"}