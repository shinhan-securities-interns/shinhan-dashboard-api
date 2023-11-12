from fastapi import APIRouter
import services.StockTalkService as StockTalkService
router = APIRouter()

@router.get("/")
async def stockTalkGetBoard(code: str):

    return {"board" : StockTalkService.crawlStockTalkBoard(code)}
