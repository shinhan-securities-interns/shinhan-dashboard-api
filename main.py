import asyncio
import json
import os
import sys
import logging
import anyio
import httpx
from apscheduler.triggers.interval import IntervalTrigger
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks
from database.RedisDriver import RedisDriver
import services.FinancialStatementService as FinancialStatementService
import services.StockTalkService as StockTalkService
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from databases import Database
current_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_directory, "controllers"))
sys.path.append(os.path.join(current_directory, "services"))

app = FastAPI()

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6322')


DATABASE_URL = "mysql+pymysql://admin:abcd1234!@database-1.coibefbchrij.ap-northeast-2.rds.amazonaws.com:3306/mys2d"
database = Database(DATABASE_URL)


def get_app():
    return app

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # 로그 파일 경로 및 로그 레벨 설정
    logging.basicConfig(
        filename='app.log',  # 로그 파일 경로
        level=logging.DEBUG  # 원하는 로그 레벨 설정 (예: ERROR, INFO, DEBUG 등)
    )

    print("startup_event")
    try:
        if not hasattr(app.state, 'redis_KospiKosdaq_contents'):
            app.state.redis_KospiKosdaq_contents = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/0")

        # 이미 추가한 속성인지 확인한 후 추가
        if not hasattr(app.state, 'redis_stocktalk_contents'):
            app.state.redis_stocktalk_contents = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/3")

        if not hasattr(app.state, 'revenue_AnnualAndQuarter'):
            app.state.revenue_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/4")

        if not hasattr(app.state, 'operating_profit_AnnualAndQuarter'):
            app.state.operating_profit_AnnualAndQuarter = RedisDriver(
                f"{REDIS_HOST}:{REDIS_PORT}/5")

        if not hasattr(app.state, 'net_profit_AnnualAndQuarter'):
            app.state.net_profit_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/6")

        if not hasattr(app.state, 'debt_ratio_AnnualAndQuarter'):
            app.state.debt_ratio_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/7")

        if not hasattr(app.state, 'per_AnnualAndQuarter'):
            app.state.per_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/8")

        if not hasattr(app.state, 'pbr_AnnualAndQuarter'):
            app.state.pbr_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/9")

        if not hasattr(app.state, 'totalFinancialInfo_AnnualAndQuarter'):
            app.state.totalFinancialInfo_AnnualAndQuarter = RedisDriver(
                f"{REDIS_HOST}:{REDIS_PORT}/10")

        if not hasattr(app.state, 'totalYearly_AnnualAndQuarter'):
            app.state.totalYearly_AnnualAndQuarter = RedisDriver(f"{REDIS_HOST}:{REDIS_PORT}/11")

        app.state.http_client = httpx.AsyncClient()
        asyncio.create_task(cacheKospiKosdaq())
        await database.connect()


    except Exception as e:
        print(f"An error occurred during startup: {e}")


@app.get("/prediction/kospi/kosdaq")
async def read_latest_kospi():
    kospi_query = "SELECT kospi FROM prediction ORDER BY created_at DESC LIMIT 1"
    kosdaq_query = "SELECT kosdaq FROM prediction ORDER BY created_at DESC LIMIT 1"

    kospi_result = await database.fetch_one(kospi_query)
    kosdaq_result = await database.fetch_one(kosdaq_query)

    # 각 결과에서 'kospi' 및 'kosdaq' 필드의 값 추출
    kospi_prediction = kospi_result["kospi"] if kospi_result else None
    kosdaq_prediction = kosdaq_result["kosdaq"] if kosdaq_result else None

    return {
        "kospi_prediction": kospi_prediction,
        "kosdaq_prediction": kosdaq_prediction
    }


@app.get("/stock-talk/{code}")
async def crawl_stock_talk(code: str, background_tasks: BackgroundTasks):
    try:
        result = await StockTalkService.getCrawlStockTalkBoard(code)
        selected_result = result[:-3]

        response_data = {"board": selected_result}

        print(response_data)

        idx = 0
        inputQueue = asyncio.Queue()

        async def process_item(item, idx):
            try:
                stockTalkPostUrl = item["href"]
                print("stockTalkPostUrl : " + stockTalkPostUrl)

                for i in range(19):
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

async def cacheKospiKosdaq():
    try:
        basic_url = "https://finance.naver.com/sise/"
        async with httpx.AsyncClient() as client:
            response = await client.get(basic_url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()


        source = response.text

        soup = BeautifulSoup(source, 'html.parser')

        kospi_now = soup.find(id="KOSPI_now").get_text()

        # "mnu" 클래스를 가진 요소를 찾음
        mnu_element = soup.find('a', class_="mnu")
        kospi_ud = mnu_element.find_all(recursive=False)[-1].get_text()
        kospi_ud = kospi_ud.replace("\n", "")
        kospi_ud = kospi_ud[:-2]

        kospi_num = kospi_ud.split(" ")[0]
        kospi_ratio = kospi_ud.split(" ")[1]

        kosdaq_now = soup.find(id="KOSDAQ_now").get_text()

        mnu2_element = soup.find('a', class_="mnu2")
        kosdaq_ud = mnu2_element.find_all(recursive=False)[-1].get_text()
        print(kosdaq_ud)

        kosdaq_ud = kosdaq_ud.replace("\n", "")
        kosdaq_ud = kosdaq_ud[:-2]

        kosdaq_num = kosdaq_ud.split(" ")[0]
        kosdaq_ratio = kosdaq_ud.split(" ")[1]

        await app.state.redis_KospiKosdaq_contents.setKey("kospi_now", kospi_now, 60 * 60 * 24)
        await app.state.redis_KospiKosdaq_contents.setKey("kospi_num", kospi_num, 60 * 60 * 24)
        await app.state.redis_KospiKosdaq_contents.setKey("kospi_ratio", kospi_ratio, 60 * 60 * 24)

        await app.state.redis_KospiKosdaq_contents.setKey("kosdaq_now", kosdaq_now, 60 * 60 * 24)
        await app.state.redis_KospiKosdaq_contents.setKey("kosdaq_num", kosdaq_num, 60 * 60 * 24)
        await app.state.redis_KospiKosdaq_contents.setKey("kosdaq_ratio", kosdaq_ratio, 60 * 60 * 24)


    except Exception as e:
        print(f"오류 발생: {e}")
        return None

@app.get("/kospi/kosdaq")
async def getKospiKosdaq():
    return {
        "kospi_now": await app.state.redis_KospiKosdaq_contents.getKey("kospi_now"),
        "kospi_num": await app.state.redis_KospiKosdaq_contents.getKey("kospi_num"),
        "kospi_ratio": await app.state.redis_KospiKosdaq_contents.getKey("kospi_ratio"),

        "kosdaq_now": await app.state.redis_KospiKosdaq_contents.getKey("kosdaq_now"),
        "kosdaq_num": await app.state.redis_KospiKosdaq_contents.getKey("kosdaq_num"),
        "kosdaq_ratio": await app.state.redis_KospiKosdaq_contents.getKey("kosdaq_ratio")
    }

scheduler = AsyncIOScheduler()
scheduler.add_job(cacheKospiKosdaq, IntervalTrigger(seconds=2))

# 스케줄러 시작
scheduler.start()

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

        if (len(result) == 0):
            return {"매출액(억원) _최근 연간 실적" : "null"}

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

        if (len(result) == 0):
            return {"매출액(억원)_최근 분기 실적": "null"}

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

        if (len(result) == 0):
            return {"영업이익(억원)_최근 연간 실적": "null"}

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

        if (len(result) == 0):
            return {"영업이익(억원)_최근 분기 실적": "null"}

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

        if (len(result) == 0):
            return {"당기순이익(억원)_최근 연간 실적": "null"}

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

        if (len(result) == 0):
            return {"당기순이익(억원)_최근 분기 실적": "null"}

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.net_profit_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"당기순이익(억원)_최근 분기 실적": result}

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

        if (len(result) == 0):
            return {"PER(배)_최근 연간 실적": "null"}

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

        if (len(result) == 0):
            return {"PER(배)_최근 분기 실적": "null"}

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.per_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"PER(배)_최근 분기 실적": result}

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

        if(len(year_annual_info) == 0):
            return {"최근 연간 실적 총계 - 기준 : 재무정보": "null"}

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

        if(len(year_annual_info) == 0):
            return {"최근 분기 실적 총계 - 기준 : 재무정보": "null"}

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

        if(len(result) == 0):
            return {"최근 연간 실적 총계 - 기준 : 연도": "null"}

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

        if (len(result) == 0):
            return {"최근 분기 실적 총계 - 기준 : 연도": "null"}

        # 결과를 JSON 형식으로 직렬화하여 Redis에 저장
        json_result = json.dumps(result)

        # 결과를 캐시에 저장
        await app.state.totalYearly_AnnualAndQuarter.setKey(cache_key, json_result, 60 * 60 * 24)

    response_data = {"최근 분기 실적 총계 - 기준 : 연도": result}

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

