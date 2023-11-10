from utils import CrawlDataFromNaverFinance as crawl

# get stock
def crawlStockTalkBoard(code):
    url = ("https://finance.naver.com/item/board.naver")
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)
    titles = crawledResponse.find_all('td', class_='title')
    stripped_titles = [title.text.strip() for title in titles]


    return stripped_titles