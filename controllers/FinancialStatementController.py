from fastapi import APIRouter
import services.FinancialStatementService as FinancialStatementService
router = APIRouter()


#최근 연간 실적 총계 - 기준 : 연도
@router.get("/total_yearly/annual_performance")
async def getTotalYearlyAnnual(code: str):

    total_yearly_annual = FinancialStatementService.crawlTotalYearlyAnnual(code)

    return {"최근 연간 실적 총계 - 기준 : 연도" : total_yearly_annual}

#최근 분기 실적 총계 - 기준 : 연도
@router.get("/total_yearly/quarter_performance")
async def getTotalYearlyQuarter(code: str):

    total_yearly_quarter = FinancialStatementService.crawlTotalYearlyQuarter(code)

    return {"최근 분기 실적 총계 - 기준 : 연도" : total_yearly_quarter}

#####

#최근 연간 실적 총계 - 기준 : 재무정보
@router.get("/total_financialInfo/annual_performance")
async def getTotalFinancialInfoAnnual(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    total_financialInfo_annual = FinancialStatementService.crawlTotalFinancialInfoAnnual(code, year_annual_info)


    return {"최근 연간 실적 총계 - 기준 : 재무정보" : total_financialInfo_annual}

#최근 분기 실적 총계 - 기준 : 재무정보
@router.get("/total_financialInfo/quarter_performance")
async def getTotalFinancialInfoQuarter(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    total_financialInfo_quarter = FinancialStatementService.crawlTotalFinancialInfoQuarter(code, year_quarter_info)

    return {"최근 분기 실적 총계 - 기준 : 재무정보" : total_financialInfo_quarter}

#####

#매출액(억원)
@router.get("/revenue/annual_performance")
async def getAnnualRevenue(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal8'
    revenue_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"매출액(억원) _최근 연간 실적" : revenue_annual_dict}

@router.get("/revenue/quarter_performance")
async def getQuarterRevenue(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal8'
    revenue_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"매출액(억원) 최근 분기 실적" : revenue_quarter_dict}

#영억이익(억원)
@router.get("/operating_profit/annual_performance")
async def getAnnualOperatingProfit(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal9'
    operating_profit_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"영업이익(억원) _최근 연간 실적" : operating_profit_annual_dict}

@router.get("/operating_profit/quarter_performance")
async def getQuarterOperatingProfit(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal9'
    operating_profit_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"영업이익(억원) 최근 분기 실적" : operating_profit_quarter_dict}

#당기순이익(억원)
@router.get("/net_profit/annual_performance")
async def getAnnualNetProfit(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal10'
    net_profit_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"당기순이익(억원) 최근 연간 실적" : net_profit_annual_dict}

@router.get("/net_profit/quarter_performance")
async def getQuarterNetProfit(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal10'
    net_profit_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"당기순이익(억원) 최근 분기 실적" : net_profit_quarter_dict}

#영업이익률(%)
@router.get("/operating_profit_margin/annual_performance")
async def getAnnualOperatingProfitMargin(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal11'
    operating_profit_margin_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"영업이익률(%) 최근 연간 실적" : operating_profit_margin_annual_dict}

@router.get("/operating_profit_margin/quarter_performance")
async def getQuarterOperatingProfitMargin(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal11'
    operating_profit_margin_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"영업이익률(%) 최근 분기 실적" : operating_profit_margin_quarter_dict}

#순이익률(%)
@router.get("/net_profit_margin/annual_performance")
async def getAnnualNetProfitMargin(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal12'
    net_profit_margin_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"순이익률(%) 최근 연간 실적" : net_profit_margin_annual_dict}

@router.get("/net_profit_margin/quarter_performance")
async def getQuarterNetProfitMargin(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal12'
    net_profit_margin_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"순이익률(%) 최근 분기 실적" : net_profit_margin_quarter_dict}

#ROE(%)
@router.get("/roe/annual_performance")
async def getAnnualROE(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal13'
    roe_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"ROE(%) 최근 연간 실적" : roe_annual_dict}

@router.get("/roe/quarter_performance")
async def getQuarterROE(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal13'
    roe_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"ROE(%) 최근 분기 실적" : roe_quarter_dict}

#부채비율(%)
@router.get("/debt_ratio/annual_performance")
async def getAnnualDebtRatio(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal14'
    debt_ratio_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"부채비율(%) 최근 연간 실적" : debt_ratio_annual_dict}

@router.get("/debt_ratio/quarter_performance")
async def getQuarterDebtRatio(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal14'
    debt_ratio_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"부채비율(%) 최근 분기 실적" : debt_ratio_quarter_dict}

#당좌비율(%)
@router.get("/quick_ratio/annual_performance")
async def getAnnualQuickRatio(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal15'
    quick_ratio_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"당좌비율(%) 최근 연간 실적" : quick_ratio_annual_dict}

@router.get("/quick_ratio/quarter_performance")
async def getQuarterQuickRatio(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal15'
    quick_ratio_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"당좌비율(%) 최근 분기 실적" : quick_ratio_quarter_dict}

#유보욜(%)
@router.get("/retention_ratio/annual_performance")
async def getAnnualRetentionRatio(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal16'
    retention_ratio_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"유보욜(%) 최근 연간 실적" : retention_ratio_annual_dict}

@router.get("/retention_ratio/quarter_performance")
async def getQuarterRetentionRatio(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal16'
    retention_ratio_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"유보욜(%) 최근 분기 실적" : retention_ratio_quarter_dict}

#EPS(원)
@router.get("/eps/annual_performance")
async def getAnnualEPS(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal17'
    eps_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"EPS(원) 최근 연간 실적" : eps_annual_dict}

@router.get("/eps/quarter_performance")
async def getQuarterEPS(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal17'
    eps_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"EPS(원) 최근 분기 실적" : eps_quarter_dict}

#PER(배)
@router.get("/per/annual_performance")
async def getAnnualPER(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal18'
    per_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"PER(배) 최근 연간 실적" : per_annual_dict}

@router.get("/per/quarter_performance")
async def getQuarterPER(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal18'
    per_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"PER(배) 최근 분기 실적" : per_quarter_dict}

#BPS(원)
@router.get("/bps/annual_performance")
async def getAnnualBPS(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal19'
    bps_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"BPS(원) 최근 연간 실적" : bps_annual_dict}

@router.get("/bps/quarter_performance")
async def getQuarterBPS(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal19'
    bps_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"BPS(원) 최근 분기 실적" : bps_quarter_dict}

#PBR(배)
@router.get("/pbr/annual_performance")
async def getAnnualPBR(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal20'
    pbr_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"PBR(배) 최근 연간 실적" : pbr_annual_dict}

@router.get("/pbr/quarter_performance")
async def getQuarterPBR(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal20'
    pbr_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"PBR(배) 최근 분기 실적" : pbr_quarter_dict}

#주당배당금(원)
@router.get("/dividend_per_share/annual_performance")
async def getAnnualDividendPerShare(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal21'
    dividend_per_share_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"주당배당금(원) 최근 연간 실적" : dividend_per_share_annual_dict}

@router.get("/dividend_per_share/quarter_performance")
async def getQuarterDividendPerShare(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal21'
    dividend_per_share_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"주당배당금(원) 최근 분기 실적" : dividend_per_share_quarter_dict}

#시가배당률(%)
@router.get("/dividend_yield/annual_performance")
async def getAnnualDividendYield(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal22'
    dividend_yield_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"시가배당률(%) 최근 연간 실적" : dividend_yield_annual_dict}

@router.get("/dividend_yield/quarter_performance")
async def getQuarterDividendYield(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal22'
    dividend_yield_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"시가배당률(%) 최근 분기 실적" : dividend_yield_quarter_dict}

#배당성향(%)
@router.get("/dividend_payout_ratio/annual_performance")
async def getAnnualDividendPayoutRatio(code: str):

    year_annual_info = FinancialStatementService.crawlAnnualYearInfo(code)
    financial_info = 'h_th2 th_cop_anal23'
    dividend_payout_ratio_annual_dict = FinancialStatementService.crawlAnnualInfo(code, year_annual_info, financial_info)


    return {"배당성향(%) 최근 연간 실적" : dividend_payout_ratio_annual_dict}

@router.get("/dividend_payout_ratio/quarter_performance")
async def getQuarterDividendPayoutRatio(code: str):

    year_quarter_info = FinancialStatementService.crawlQuarterYearInfo(code)
    financial_info = 'h_th2 th_cop_anal23'
    dividend_payout_ratio_quarter_dict = FinancialStatementService.crawlQuarterInfo(code, year_quarter_info, financial_info)

    return {"배당성향(%) 최근 분기 실적" : dividend_payout_ratio_quarter_dict}


