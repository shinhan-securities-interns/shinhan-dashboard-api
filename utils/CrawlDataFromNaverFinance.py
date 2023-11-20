
import requests
from bs4 import BeautifulSoup

def CrawlDataFromNaverFinance(url, code):
    try:
        # 웹 페이지에 요청을 보내고 HTML을 가져옴
        response = requests.get(url + "?code=" + code, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        # return http status

        crawledResponse = BeautifulSoup(response.text, 'html.parser')

        return crawledResponse
    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def GetKospiKosdaqValues():
    try:
        basic_url = "https://finance.naver.com/sise/"
        response = requests.get(basic_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        source = response.text

        soup = BeautifulSoup(source, 'html.parser')

        kospi_now = soup.find(id="KOSPI_now").get_text()


        # "mnu" 클래스를 가진 요소를 찾음
        mnu_element = soup.find('a', class_="mnu")
        kospi_ud = mnu_element.find_all(recursive=False)[-1].get_text()
        kospi_ud = kospi_ud.replace("\n", "")
        kospi_ud = kospi_ud[:-2]

        kosdaq_now = soup.find(id="KOSDAQ_now").get_text()

        mnu2_element = soup.find('a', class_="mnu2")
        kosdaq_ud = mnu2_element.find_all(recursive=False)[-1].get_text()
        kosdaq_ud = kosdaq_ud.replace("\n", "")
        kosdaq_ud = kospi_ud[:-2]


        return {
            "kospi_now" : kospi_now,
            "kospi_ud" : kospi_ud,
            "kosdaq_now": kosdaq_now,
            "kosdaq_ud": kosdaq_ud
        }

    except Exception as e:
        print(f"오류 발생: {e}")
        return None



