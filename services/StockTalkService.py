import httpx

from utils import CrawlDataFromNaverFinance as crawl

# get stock
async def getCrawlStockTalkBoard(code):
    url = "https://finance.naver.com/item/board.naver"
    crawledResponse = crawl.CrawlDataFromNaverFinance(url, code)

    # 결과를 저장할 빈 리스트
    result_list = []

    table = crawledResponse.find('table', {'class': 'type2'})
    tt = table.select('tbody > tr')

    for i in range(2, len(tt)):
        if len(tt[i].select('td > span')) > 0:
            date = tt[i].select('td > span')[0].text
            title = tt[i].select('td.title > a')[0]['title']
            writer = tt[i].select('td.p11')[0].text.replace('\t', '').replace('\n', '')
            views = tt[i].select('td > span')[1].text
            pos = tt[i].select('td > strong')[0].text
            neg = tt[i].select('td > strong')[1].text
            href = tt[i].select('td.title > a')[0]['href']

            readUrl = 'https://finance.naver.com/'
            getStockTalkPostUrl = readUrl + href

            result_dict = {'date': date, 'title': title, 'writer': writer, 'views': views, 'like': pos, 'dislike': neg, 'href': getStockTalkPostUrl}
            result_list.append(result_dict)

    return result_list



async def getStockTalk(code, idx):
    key = code + "_" + str(idx)
    contents = await app.state.redis_stocktalk_contents.getKey(key)
    if contents:
        return contents
    else:
        return None