from utils import CrawlDataFromNaverFinance as crawl

async def crawlAnnualYearInfo(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    # div 클래스 이름이 "section cop_analysis"인 섹션을 찾음
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    # 2번째 tr 요소를 찾음 
    second_tr = cop_analysis_section.find_all("tr")[1]

    # 날짜 정보 가져오기 
    col_headers = second_tr.find_all("th", {"scope": "col"})
    year_annual_info = [th.text.strip() for th in col_headers[:4]]

    return year_annual_info


async def crawlQuarterYearInfo(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    second_tr = cop_analysis_section.find_all("tr")[1]

    col_headers = second_tr.find_all("th", {"scope": "col"})
    year_quarter_info = [th.text.strip() for th in col_headers[4:10]]

    return year_quarter_info

# get Corporate Performance Analysis  => FinancialInformation_RecentAnnualPerformance (재무 정보별 최근 연간 실적)
async def crawlAnnualInfo(code, year_info, financial_info):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    th_elements = crawledResponse.find_all('th', class_= financial_info)

    #딕셔너리로 저장
    annual_dict = {}

    # 각 th 요소에 대응하는 연속된 4개의 td 요소를 가져오고 출력
    for th_element in th_elements:
        # th 요소의 부모인 tr 요소에서 연속된 4개의 td 요소를 가져옴
        td_elements = th_element.find_parent("tr").find_all("td")
        
        values = [td.text.strip().replace(',','') for td in td_elements[:4]]

        # 헤더 이름을 키로하고 값을 값으로하는 딕셔너리 항목 만들기
        entry = dict(zip(year_info, values))

        
        # entry를 revenue_dict에 추가
        annual_dict.update(entry)

        print(annual_dict)

    return annual_dict


# get Corporate Performance Analysis  => FinancialInformation_RecentQuarterlyPerformance (재무 정보별 최근 분기 실적)
async def crawlQuarterInfo(code, year_info, financial_info):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    th_elements = crawledResponse.find_all('th', class_= financial_info)
    
    # 딕셔너리로 저장
    quarter_dict = {}

  
    for th_element in th_elements:
     
        td_elements = th_element.find_parent("tr").find_all("td")
        values = [td.text.strip().replace(',','') for td in td_elements[4:11]]
        entry = dict(zip(year_info, values))

        
        quarter_dict.update(entry)
        print(quarter_dict)

    return quarter_dict

## get Corporate Performance Analysis  => Total_RecentAnnualPerformance (최근 연간 실적 총계 - 기준 : 재무정보)
async def crawlTotalFinancialInfoAnnual(code, year_info):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    tbody = cop_analysis_section.find('tbody')

    # 딕셔너리로 저장
    annual_dict = {}
    financial_info_dict = {}

    for tr in tbody.find_all('tr'):
        th_text = tr.find('th').text.strip()

        td_elements = tr.find_all('td')
        td_values = [td.text.strip().replace(',','') for td in td_elements[:4]]

        entry = dict(zip(year_info, td_values))
        financial_info_dict[th_text] = entry
        annual_dict.update(financial_info_dict)

    return annual_dict

# get Corporate Performance Analysis  => Total_RecentQuarterlyPerformance(최근 분기 실적 총계 - 기준 : 재무정보)
async def crawlTotalFinancialInfoQuarter(code, year_info):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    tbody = cop_analysis_section.find('tbody')

    # 딕셔너리로 저장
    quarter_dict = {}
    financial_info_dict = {}

    for tr in tbody.find_all('tr'):
        th_text = tr.find('th').text.strip()

        td_elements = tr.find_all('td')
        td_values = [td.text.strip().replace(',','') for td in td_elements[4:11]]

        entry = dict(zip(year_info, td_values))
        financial_info_dict[th_text] = entry
        quarter_dict.update(financial_info_dict)

    return quarter_dict

## get Corporate Performance Analysis  => Total_RecentAnnualPerformance (최근 연간 실적 총계 - 기준 : 연도)
async def crawlTotalYearlyAnnual(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    
    # 연도 정보를 가져오기
    annual_year_info = crawlAnnualYearInfo(code)

    annual_info = {}

    if cop_analysis_section:
        tbody = cop_analysis_section.find('tbody')
        
        for tr in tbody.find_all('tr'):
            th_tag = tr.find('th')
            td_list = tr.find_all('td')
            
            if th_tag is not None and len(td_list) >= 4:
                key = th_tag.text.strip()
                values = [td.text.strip().replace(',', '') for td in td_list[0:4]]
                
                for year in annual_year_info:
                    # 해당 연도의 딕셔너리가 없으면 먼저 생성
                    if year not in annual_info:
                        annual_info[year] = {}
                    
                    # 해당 연도의 딕셔너리에 값을 추가
                    annual_info[year][key] = values[annual_year_info.index(year)]

    return annual_info

## get Corporate Performance Analysis  => Total_RecentAnnualPerformance (최근 분기 실적 총계 - 기준 : 연도)
async def crawlTotalYearlyQuarter(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    
    quarter_year_info = crawlQuarterYearInfo(code)

    quarter_info = {}

    if cop_analysis_section:
        tbody = cop_analysis_section.find('tbody')
        
        for tr in tbody.find_all('tr'):
            th_tag = tr.find('th')
            td_list = tr.find_all('td')
            
            if th_tag is not None and len(td_list) >= 4:
                key = th_tag.text.strip()
                values = [td.text.strip().replace(',', '') for td in td_list[4:10]]
                
                for year in quarter_year_info:
                    if year not in quarter_info:
                        quarter_info[year] = {}
                    
                    quarter_info[year][key] = values[quarter_year_info.index(year)]

    return quarter_info