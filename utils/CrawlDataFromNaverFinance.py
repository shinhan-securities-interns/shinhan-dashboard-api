
import requests
from bs4 import BeautifulSoup

def CrawlDataFromNaverFinance(url, code):
    try:
        # 웹 페이지에 요청을 보내고 HTML을 가져옴
        response = requests.get(url + "?code=" + code, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        crawledResponse = BeautifulSoup(response.text, 'html.parser')
        print(crawledResponse)
        return crawledResponse
    except Exception as e:
        print(f"오류 발생: {e}")
        return None