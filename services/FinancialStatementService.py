from utils import CrawlDataFromNaverFinance as crawl

def crawlAnnualYearInfo(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    # div 클래스 이름이 "section cop_analysis"인 섹션을 찾음
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    # 2번째 tr 요소를 찾음 (인덱스는 0부터 시작하므로 인덱스 1이 2번째를 나타냄)
    second_tr = cop_analysis_section.find_all("tr")[1]

    # 날짜 정보 가져오기 
    col_headers = second_tr.find_all("th", {"scope": "col"})
    year_annual_info = [th.text.strip() for th in col_headers[:4]]

    return year_annual_info


def crawlQuaterYearInfo(code):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    # div 클래스 이름이 "section cop_analysis"인 섹션을 찾음
    cop_analysis_section = crawledResponse.find("div", class_="section cop_analysis")
    # 2번째 tr 요소를 찾음 (인덱스는 0부터 시작하므로 인덱스 1이 2번째를 나타냄)
    second_tr = cop_analysis_section.find_all("tr")[1]

    # 날짜 정보 가져오기 
    col_headers = second_tr.find_all("th", {"scope": "col"})
    year_quarter_info = [th.text.strip() for th in col_headers[4:10]]

    return year_quarter_info

def crawlAnnualInfo(code, year_info, financial_info):
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

        # 헤더 이름을 키로하고 값을 값으로하는 딕셔너리 항목을 만듭니다.
        entry = dict(zip(year_info, values))

        
        # entry를 revenue_dict에 추가합니다.
        annual_dict.update(entry)

        print(annual_dict)

    return annual_dict


# get Corporate Performance Analysis  => RecentQuarterlyPerformance (최근 분기 실적)
def crawlQuarterInfo(code, year_info, financial_info):
    url = ("https://finance.naver.com/item/main.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    
    th_elements = crawledResponse.find_all('th', class_= financial_info)
    
    # 딕셔너리로 저장
    quarter_dict = {}

    # 각 th 요소에 대응하는 연속된 4개의 td 요소를 가져오고 출력
    for th_element in th_elements:
        # th 요소의 부모인 tr 요소에서 연속된 4개의 td 요소를 가져옴
        td_elements = th_element.find_parent("tr").find_all("td")
        
        values = [td.text.strip().replace(',','') for td in td_elements[4:11]]

        # 헤더 이름을 키로하고 값을 값으로하는 딕셔너리 항목을 만듭니다.
        entry = dict(zip(year_info, values))

        
        # entry를 revenue_dict에 추가합니다.
        quarter_dict.update(entry)

        print(quarter_dict)

    return quarter_dict

