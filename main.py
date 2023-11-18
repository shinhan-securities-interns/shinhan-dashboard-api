import asyncio
import json
import os
import sys
import logging
import anyio
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks
import database.RedisDriver
import services.FinancialStatementService as FinancialStatementService
import services.StockTalkService as StockTalkService
from controllers.FinancialStatementController import router as financial_statement_router
from controllers.IndiStockController import router as indi_stock_router

current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_directory, "controllers"))
sys.path.append(os.path.join(current_directory, "services"))

app = FastAPI()

app.include_router(indi_stock_router, prefix="/indi-stock", tags=["indi-stock"])
app.include_router(financial_statement_router, prefix="/financial-statement", tags=["financial-statement"])

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')

def get_app():
    return app

@app.on_event("startup")
async def startup_event():
    # 로그 파일 경로 및 로그 레벨 설정
    logging.basicConfig(
        filename='app.log',  # 로그 파일 경로
        level=logging.DEBUG  # 원하는 로그 레벨 설정 (예: ERROR, INFO, DEBUG 등)
    )

    print("startup_event")
    try:
        app.state.redis_stocktalk_contents = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/3")
        app.state.http_client = httpx.AsyncClient()

        app.state.revenue_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/4")
        app.state.operating_profit_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/5")
        app.state.net_profit_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/6")
        app.state.debt_ratio_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/7")
        app.state.per_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/8")
        app.state.pbr_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/9")

        app.state.totalFinancialInfo_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/10")
        app.state.totalYearly_AnnualAndQuarter = database.RedisDriver.RedisDriver(f"{REDIS_HOST}:6322/11")
    except Exception as e:
        print(f"An error occurred during startup: {e}")

@app.get("/stock-talk/{code}")
async def crawl_stock_talk(code: str, background_tasks: BackgroundTasks):
    try:
        result = await StockTalkService.getCrawlStockTalkBoard(code)
        response_data = {"board": result}
        print(response_data)

        idx = 0
        inputQueue = asyncio.Queue()

        async def process_item(item, idx):
            try:
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
            except Exception as e:
                print(f"An error occurred during processing: {e}")

        async with anyio.create_task_group() as tg:
            for idx, item in enumerate(result):
                tg.start_soon(process_item, item, idx)

        await cacheToRedis(inputQueue)
        return response_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}

async def cacheToRedis(inputQueue):
    try:
        results = []

        while not inputQueue.empty():
            idx, item = await inputQueue.get()
            results.append((idx, item))

        results.sort(key=lambda x: x[0])

        for _, item in results:
            await app.state.redis_stocktalk_contents.setKey(item, 0, 60 * 60 * 24)
    except Exception as e:
        print(f"An error occurred while caching to Redis: {e}")

@app.get("/stock-talk/{code}/contents/{index}")
async def getContentsFromRedis(code: str, index: str):
    try:
        if await app.state.redis_stocktalk_contents.getContentsWithCodeAndIndex(code + "_" + index) is None:

            result = await StockTalkService.getCrawlStockTalkBoard(code)
            response_data = {"board": result}
            print(response_data)

            idx = 0
            inputQueue = asyncio.Queue()

            async def process_item(item, idx):
                try:
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
                except Exception as e:
                    print(f"An error occurred during processing: {e}")

            async with anyio.create_task_group() as tg:
                for idx, item in enumerate(result):
                    tg.start_soon(process_item, item, idx)

            await cacheToRedis(inputQueue)

        contents = await app.state.redis_stocktalk_contents.getContentsWithCodeAndIndex(code + "_" + index)

        contentsResponse = {
            "code" : code,
            "index" : index,
            "contents": contents
        }

        return contentsResponse
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error": str(e)}


##################

## 매출액(억원)
@app.get("/revenue/annual/{code}")
async def getAnnualRevenue(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_Revenue_Annual"
    cached_data = await app.state.revenue_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal8'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.revenue_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"매출액(억원) _최근 연간 실적": result}
    #print(response_data)

    return response_data

@app.get("/revenue/quarter/{code}")
async def getQuarterRevenue(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_Revenue_Quarter"
    cached_data = await app.state.revenue_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal8'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.revenue_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"매출액(억원)_최근 분기 실적": result}
    #print(response_data)

    return response_data


#영업이익(억원)
@app.get("/operating_profit/annual/{code}")
async def getAnnualOperatingProfit(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_OperatingProfit_Annual"
    cached_data = await app.state.operating_profit_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal9'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.operating_profit_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"영업이익(억원)_최근 연간 실적": result}

    return response_data

@app.get("/operating_profit/quarter/{code}")
async def getQuarterOperatingProfit(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_OperatingProfit_Quarter"
    cached_data = await app.state.operating_profit_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal9'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.operating_profit_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"영업이익(억원)_최근 분기 실적": result}

    return response_data


#당기순이익(억원)
@app.get("/net_profit/annual/{code}")
async def getAnnualNetProfit(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_NetProfit_Annual"
    cached_data = await app.state.net_profit_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal10'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.net_profit_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"당기순이익(억원)_최근 연간 실적": result}

    return response_data

@app.get("/net_profit/quarter/{code}")
async def getQuarterNetProfit(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_NetProfit_Quarter"
    cached_data = await app.state.net_profit_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal10'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.net_profit_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"당기순이익(억원)_최근 분기 실적": result}

    return response_data


#부채비율(%)
@app.get("/debt_ratio/annual/{code}")
async def getAnnualDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_DebtRatio_Annual"
    cached_data = await app.state.debt_ratio_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal14'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.debt_ratio_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"부채비율(%)_최근 연간 실적": result}

    return response_data

@app.get("/debt_ratio/quarter/{code}")
async def getQuarterDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_DebtRatio_Quarter"
    cached_data = await app.state.debt_ratio_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal14'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.debt_ratio_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"부채비율(%)_최근 분기 실적": result}

    return response_data


#PER(배)
@app.get("/per/annual/{code}")
async def getAnnualDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_PER_Annual"
    cached_data = await app.state.per_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal20'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.per_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"PER(배)_최근 연간 실적": result}

    return response_data

@app.get("/per/quarter/{code}")
async def getQuarterDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_PER_Quarter"
    cached_data = await app.state.per_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal20'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.per_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"PER(배)_최근 분기 실적": result}

    return response_data


#PBR(배)
@app.get("/pbr/annual/{code}")
async def getAnnualDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_PBR_Annual"
    cached_data = await app.state.pbr_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        financial_info = 'h_th2 th_cop_anal21'
        result = await FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.pbr_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"PBR(배)_최근 연간 실적": result}

    return response_data

@app.get("/pbr/quarter/{code}")
async def getQuarterDebtRatio(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_PBR_Quarter"
    cached_data = await app.state.pbr_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        financial_info = 'h_th2 th_cop_anal21'
        result = await FinancialStatementService.crawlQuarterInfo(code, year_annual_info, financial_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.pbr_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"PBR(배)_최근 분기 실적": result}

    return response_data

#######################################

# Total Financial Info (최근 연간 실적 총계 - 기준 : 재무정보)
@app.get("/total_financial_info/annual/{code}")
async def getAnnualTotalFinancialInfo(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_TotalFinancialInfo_Annual"
    cached_data = await app.state.totalFinancialInfo_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlAnnualYearInfo(code)
        result = await FinancialStatementService.crawlTotalFinancialInfoAnnual(code, year_annual_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.totalFinancialInfo_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"최근 연간 실적 총계 - 기준 : 재무정보": result}

    return response_data

# Total Financial Info (최근 분기 실적 총계 - 기준 : 재무정보)
@app.get("/total_financial_info/quarter/{code}")
async def getQuarterTotalFinancialInfo(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_TotalFinancialInfo_Quarter"
    cached_data = await app.state.totalFinancialInfo_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        year_annual_info = await FinancialStatementService.crawlQuarterYearInfo(code)
        result = await FinancialStatementService.crawlTotalFinancialInfoQuarter(code, year_annual_info)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.totalFinancialInfo_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"최근 분기 실적 총계 - 기준 : 재무정보": result}

    return response_data

##########################################

# Total Yearly Info (최근 연간 실적 총계 - 기준 : 연도)
@app.get("/total_yearly/annual/{code}")
async def getAnnualTotalYearly(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_TotalYearly_Annual"
    cached_data = await app.state.totalYearly_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        result = await FinancialStatementService.crawlTotalYearlyAnnual(code)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.totalYearly_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"최근 연간 실적 총계 - 기준 : 연도": result}

    return response_data

# Total Yearly Info (최근 분기 실적 총계 - 기준 : 연도)
@app.get("/total_yearly/quarter/{code}")
async def getQuarterTotalYearly(code: str, background_tasks: BackgroundTasks):

    # Redis에서 데이터 가져오기 시도
    cache_key = f"{code}_TotalYearly_Quarter"
    cached_data = await app.state.totalYearly_AnnualAndQuarter.getKey(cache_key)

    if cached_data:
        # 캐시된 데이터가 있으면 JSON 역직렬화하여 반환
        result = json.loads(cached_data)
    else:
        # 캐시된 데이터가 없으면 데이터 생성 및 JSON 직렬화 후 Redis에 저장
        result = await FinancialStatementService.crawlTotalYearlyQuarter(code)

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.totalYearly_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"최근 분기 실적 총계 - 기준 : 연도": result}

    return response_data