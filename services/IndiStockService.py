from fastapi import FastAPI
from PyQt5.QtWidgets import *
import pandas as pd
import GiExpertControl as giLogin  # 통신모듈 - 로그인
import GiExpertControl as giStockRTTRShow
import GiExpertControl as TRShow
from dotenv import load_dotenv
import sys
import os
from datetime import datetime, timedelta
import asyncio
# load .env
load_dotenv()

INDI_ID = os.environ.get('INDI_ID')
INDI_PW = os.environ.get('INDI_PW')
INDI_PW2 = os.environ.get('INDI_PW2')

app = FastAPI()

indi_app_instance = None


class indiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("IndiExample")
        TRShow.SetQtMode(True)
        print('finish qt mode set')
        # giStockRTTRShow.RunIndiPython()
        TRShow.RunIndiPython()
        giLogin.RunIndiPython()
        print('run python')

        self.rqidD = {}
        self.data = {}


        print(giLogin.GetCommState())
        if giLogin.GetCommState() == 0:  # 정상
            print('정상')
        elif giLogin.GetCommState() == 1:  # 비정상
            print('비정상')
            # 본인의 ID 및 PW 넣으셔야 합니다.
            login_return = giLogin.StartIndi(
                INDI_ID, INDI_PW, INDI_PW2, 'C:\\SHINHAN-i\\indi\\giexpertstarter.exe')
            if login_return == True:
                print("INDI 로그인 정보", "INDI 정상 호출")
                print(giLogin.GetCommState())
            else:
                print("INDI 로그인 정보", "INDI 호출 실패")

        # self.search_stock_news()
        # time.sleep(5)
        TRShow.SetCallBack('ReceiveData', self.TRShow_ReceiveData)
        giStockRTTRShow.SetCallBack('ReceiveRTData', self.RealTimeTRShow_ReceiveRTData)

    async def stock_vi(self, stockCode: str):
        self.data = None
        TR_Name = "SY" #VI
        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, stockCode)
        rqid = TRShow.RequestData()
        print(TRShow.GetErrorMessage())
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        while self.data is None:
            # 일정 시간동안 대기하여 busy-waiting을 피합니다.
            await asyncio.sleep(1)

        return self.data



    async def chart_data(self, stockCode: str, chartType: str):
        self.data = None
        TR_Name = "TR_SCHART"

        searchCnt = "390"
        timeInterval = "1"

        if chartType == "1": #분데이터면
            startDay = "00000000"
            endDay = "99999999"

        else:
            startDay = "20000101"
            endDay = datetime.now().strftime("%Y%m%d")

        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, stockCode)
        ret = TRShow.SetSingleData(1, chartType)
        ret = TRShow.SetSingleData(2, timeInterval)
        ret = TRShow.SetSingleData(3, startDay)
        ret = TRShow.SetSingleData(4, endDay)
        ret = TRShow.SetSingleData(5, searchCnt)
        rqid = TRShow.RequestData()
        print(TRShow.GetErrorMessage())
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        while self.data is None:
            # 일정 시간동안 대기하여 busy-waiting을 피합니다.
            await asyncio.sleep(1)

        return self.data


    async def market_actions(self):

        self.data = None
        TR_Name = "IM"
        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, "*")
        rqid = TRShow.RequestData()
        print(TRShow.GetErrorMessage())
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name
        while self.data is None:
            # 일정 시간동안 대기하여 busy-waiting을 피합니다.
            await asyncio.sleep(1)

        return self.data


    # 실시간 현재가
    async def real_stock_price(self, stockCode: str):

        self.data = None
        TR_Name = "SC"
        rqid = giStockRTTRShow.RequestRTReg(TR_Name, stockCode)
        TRShow.GetErrorMessage()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        while self.data is None:
            # 일정 시간동안 대기하여 busy-waiting을 피합니다.
            await asyncio.sleep(1)

        return self.data

    # 현재가
    async def stock_price(self, stockCode: str):
        self.data = None

    # 종목 점수 조회
    async def stock_score(self, stockCode: str):

        self.data = None
        TR_Name = "TR_SDIA_M1"  ## 종목점수
        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, stockCode)
        rqid = TRShow.RequestData()

        # print(TRShow.GetErrorMessage())
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name
        while self.data is None:
            # 일정 시간동안 대기하여 busy-waiting을 피합니다.
            await asyncio.sleep(1)

        return self.data



    # TR data 처리
    def TRShow_ReceiveData(self, giCtrl, rqid):

        self.data = None
        print("in receive_Data:", rqid)
        print('recv rqid: {}->{}\n'.format(rqid, self.rqidD[rqid]))
        TR_Name = self.rqidD[rqid]
        tr_data_output = []
        output = []

        print("TR_name : ", TR_Name)

        if TR_Name == "SY":
            stockCode = str(giCtrl.GetSingleData(1)).strip()
            tradeExecutionProcessingTime = str(giCtrl.GetSingleData(2)).strip()
            volatilityInterruptionReleaseTime = str(giCtrl.GetSingleData(3)).strip()
            viApplicationCode = str(giCtrl.GetSingleData(4)).strip()
            viTypeCode = str(giCtrl.GetSingleData(5)).strip()
            staticVITriggerBasePrice = str(giCtrl.GetSingleData(6)).strip()
            viTriggerPrice = str(giCtrl.GetSingleData(7)).strip()
            staticVITriggerDeviationRate = str(giCtrl.GetSingleData(8)).strip()
            dynamicVITriggerBasePrice = str(giCtrl.GetSingleData(9)).strip()
            dynamicVITriggerDeviationRate = str(giCtrl.GetSingleData(10)).strip()

            self.data = {
                'stockCode': stockCode,
                'tradeExecutionProcessingTime': tradeExecutionProcessingTime, #매매체결처리시각
                'volatilityInterruptionReleaseTime': volatilityInterruptionReleaseTime, #VI해제시각
                'viApplicationCode': viApplicationCode, #VI적용구분코드
                'viTypeCode': viTypeCode, #VI종류코드
                'staticVITriggerBasePrice': staticVITriggerBasePrice, #정적VI 발동기준가격
                'viTriggerPrice': viTriggerPrice, #VI발동가격
                'staticVITriggerDeviationRate': staticVITriggerDeviationRate, #정적VI 발동괴리율
                'dynamicVITriggerBasePrice': dynamicVITriggerBasePrice, #동적VI 발동기준가격
                'dynamicVITriggerDeviationRate': dynamicVITriggerDeviationRate #동적VI 발동괴리율
            }


        if TR_Name == "TR_SCHART":

            self.data = None
            nCnt = giCtrl.GetMultiRowCount()
            print(TRShow.GetErrorMessage())
            print(nCnt)
            for i in range(0, nCnt):
                row_data = {
                    'date': str(giCtrl.GetMultiData(i, 0)),
                    'time': str(giCtrl.GetMultiData(i, 1)),
                    'openingPrice': str(giCtrl.GetMultiData(i, 2)),
                    'highPrice': str(giCtrl.GetMultiData(i, 3)),
                    'lowPrice': str(giCtrl.GetMultiData(i, 4)),
                    'endPrice': str(giCtrl.GetMultiData(i, 5)),
                }
                tr_data_output.append(row_data)

            self.data = tr_data_output
            print(TRShow.GetErrorMessage())

        if TR_Name == "IM":

            data = {}
            self.data = None
            print("시장조치 실시간")
            print(TRShow.GetErrorMessage())

            marketCategory = str(giCtrl.GetSingleData(0)).strip()
            action = str(giCtrl.GetSingleData(1)).strip()
            time = str(giCtrl.GetSingleData(2)).strip()
            state = str(giCtrl.GetSingleData(3)).strip()
            step = str(giCtrl.GetSingleData(4)).strip()
            referenceSecurityPriceExpansionCode = str(giCtrl.GetSingleData(5)).strip()
            expectedPriceExpansionTime = str(giCtrl.GetSingleData(6)).strip()
            message = str(giCtrl.GetSingleData(7)).strip()

            self.data = {
                'marketCategory': marketCategory,
                'action': action,
                'time': time,
                'state': state,
                'step': step,
                'referenceSecurityPriceExpansionCode': referenceSecurityPriceExpansionCode,
                'expectedPriceExpansionTime': expectedPriceExpansionTime,
                'message': message
            }

        if TR_Name == "TR_SDIA_M1":

            try:
                self.data = None
                print("종목점수조회")

                # print(TRShow.GetErrorMessage())
                stockCode = str(giCtrl.GetSingleData(0)).strip()
                stockName = str(giCtrl.GetSingleData(1)).strip()
                updateDay = str(giCtrl.GetSingleData(2)).strip()
                totalScore = str(giCtrl.GetSingleData(3)).strip()
                industryAverage = str(giCtrl.GetSingleData(8)).strip()
                rank = str(giCtrl.GetSingleData(8)).strip()
                financialScore = str(giCtrl.GetSingleData(9)).strip()
                financialAssessment = str(giCtrl.GetSingleData(10)).strip()
                presentValueScore = str(giCtrl.GetSingleData(11)).strip()
                presentValueAssessment = str(giCtrl.GetSingleData(12)).strip()
                momentumScore = str(giCtrl.GetSingleData(13)).strip()
                momentumAssessment = str(giCtrl.GetSingleData(14)).strip()
                leadingPlayer = str(giCtrl.GetSingleData(15)).strip()
                leadingPlayerAssessment = str(giCtrl.GetSingleData(16)).strip()
                stockPriceAssessment = str(giCtrl.GetSingleData(19)).strip()
                stockPriceDirection = str(giCtrl.GetSingleData(20)).strip()
                stockPriceStrength = str(giCtrl.GetSingleData(21)).strip()
                volatility = str(giCtrl.GetSingleData(22)).strip()
                tradingVolumeAssessment = str(giCtrl.GetSingleData(23)).strip()
                tradingVolumeDirection = str(giCtrl.GetSingleData(24)).strip()
                tradingVolumeStrength = str(giCtrl.GetSingleData(25)).strip()

                self.data = {
                    'stockCode': stockCode,
                    'stockName': stockName,
                    'updateDay': updateDay,
                    'totalScore': totalScore,
                    'industryAverage': industryAverage,
                    'rank': rank,
                    'financialScore': financialScore,
                    'financialAssessment': financialAssessment,
                    'presentValueScore': presentValueScore,
                    'presentValueAssessment': presentValueAssessment,
                    'momentumScore': momentumScore,
                    'momentumAssessment': momentumAssessment,
                    'leadingPlayer': leadingPlayer,
                    'leadingPlayerAssessment': leadingPlayerAssessment,
                    'stockPriceAssessment': stockPriceAssessment,
                    'stockPriceDirection': stockPriceDirection,
                    'stockPriceStrength': stockPriceStrength,
                    'volatility': volatility,
                    'tradingVolumeAssessment': tradingVolumeAssessment,
                    'tradingVolumeDirection': tradingVolumeDirection,
                    'tradingVolumeStrength': tradingVolumeStrength
                }
            except Exception as e:
                print(f"An error occurred: {e}")
                self.data = "조회할 수 없는 종목코드입니다."






    def RealTimeTRShow_ReceiveRTData(self, giCtrl, RealType):

        self.data = None
        if RealType == "SC":
            stockCode = str(giCtrl.GetSingleData(1)).strip()# 단축코드
            realPrice = str(giCtrl.GetSingleData(3)).strip()# 현재가
            dayOverDayCategory = str(giCtrl.GetSingleData(4)).strip()# 전일대비구분(상한/상승/보합/하한/하락)
            dayOverDayChange = str(giCtrl.GetSingleData(5)).strip()# 전일대비
            dayOverDayPercentage = str(giCtrl.GetSingleData(6)).strip()# 전일대비율
            cumulativeTradingVolume = str(giCtrl.GetSingleData(7)).strip()# 누적거래량
            cumulativeTradingValue = str(giCtrl.GetSingleData(8)).strip()# 누적거래대금
            unitTrasactionVolume = str(giCtrl.GetSingleData(9)).strip()# 단위체결량
            openingPrice = str(giCtrl.GetSingleData(10)).strip()# 시가
            highPrice = str(giCtrl.GetSingleData(11)).strip()# 고가
            lowPrice = str(giCtrl.GetSingleData(12)).strip()# 저가
            tradingIntensity = str(giCtrl.GetSingleData(22)).strip()# 거래강도
            trasctionIntesity = str(giCtrl.GetSingleData(24)).strip()# 체결강도

            self.data = {'stockCode': stockCode,
                         'realPrice': realPrice,
                         'dayOverDayCategory': dayOverDayCategory,
                         'dayOverDayChange': dayOverDayChange,
                         'dayOverDayChange': dayOverDayChange,
                         'dayOverDayPercentage': dayOverDayPercentage,
                         'cumulativeTradingVolume': cumulativeTradingVolume,
                         'cumulativeTradingValue': cumulativeTradingValue,
                         'unitTrasactionVolume': unitTrasactionVolume,
                         'openingPrice': openingPrice, 'highPrice': highPrice,
                         'lowPrice': lowPrice, 'tradingIntensity': tradingIntensity,
                         'trasctionIntesity': trasctionIntesity
                    }





def run_indi_app():
    global indi_app_instance
    app = QApplication(sys.argv)
    indi_app_instance = indiApp()
    sys.exit(app.exec_())