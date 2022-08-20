import requests
import re
from datetime import date
from bs4 import BeautifulSoup
from threading import Timer

class RealTimeNews(object):
    def __init__(self):
        self.last_news1 = ''
        self.last_news2 = ''
        self.temp = []


    # 기업/종목분석 뉴스
    def crawling(self):
        print("기업/종목 뉴스 crawling start")
        news_url = 'https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=402&date={}&page=1'
        main_url = 'https://finance.naver.com'
        total = []
        today = date.today().isoformat()

        req = requests.get(news_url.format("".join(today.split("-"))),
                           headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(req.text, 'html.parser')
        try:
            art_sub_dt = soup.select('dt.articleSubject')
            art_sub_dd = soup.select('dd.articleSubject')
            art_sub = art_sub_dd + art_sub_dt
            art_sum = soup.select('dd.articleSummary')
            if len(art_sub) == 0:
                pass

            for subject, summary in zip(art_sub, art_sum):
                art_link = subject.select_one('a')['href']
                art_link = art_link.replace('§', '&sect')

                req2 = requests.get(main_url+art_link, headers={'User-Agent': 'Mozilla/5.0'})
                soup2 = BeautifulSoup(req2.text, 'html.parser')

                art_title = soup2.select_one('div.article_info > h3').text.strip()
                art_wdate = soup2.select_one('span.article_date').text.strip()
                art_cont = soup2.select_one('div.articleCont').text.strip()

                if art_title == self.last_news1:
                    break

                result = {
                    'title': self.cleartext(art_title),
                    'content': self.cleartext(art_cont),
                    'wrtdate': art_wdate
                }
                total.append(result)

        except:
            pass

        try:
            if self.last_news1 == total[0]['title'] :
                print("새로운 뉴스 없음")
            else:
                for news in total:
                    print('=' * 100)
                    print(news['title'])
                    print(news['content'])

                self.last_news1 = total[0]['title']
                self.temp.extend(total)
        except IndexError:
            print("새로운 뉴스 없음")

    def crawling2(self):
        print("공시/메모 crawling start")

        news_url = 'https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=406&date={}&page=1'
        main_url = 'https://finance.naver.com'

        today = date.today().isoformat()
        total = []

        req = requests.get(news_url.format("".join(today.split("-"))),
                           headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(req.text, 'html.parser')

        art_sub = soup.select('dt.articleSubject')
        art_sum = soup.select('dd.articleSummary')
        if len(art_sub) == 0:
            pass

        for subject, summary in zip(art_sub, art_sum):
            art_link = subject.select_one('a')['href']
            art_link = art_link.replace('§', '&sect')

            req2 = requests.get(main_url + art_link, headers={'User-Agent': 'Mozilla/5.0'})
            soup2 = BeautifulSoup(req2.text, 'html.parser')

            art_title = soup2.select_one('div.article_info > h3').text.strip()
            art_wdate = soup2.select_one('span.article_date').text.strip()
            art_cont = soup2.select_one('div.articleCont').text.strip()

            if art_title == self.last_news2:
                break

            result = {
                'title': self.cleartext(art_title),
                'content': self.cleartext(art_cont),
                'wrtdate': art_wdate
            }
            total.append(result)
        try:
            if self.last_news2 == total[0]['title'] :
                print("새로운 뉴스 없음")
            else:
                for news in total:
                    print('='*100)
                    print(news['title'])
                    print(news['content'])
                    print(news['wrtdate'])
                self.last_news2 = total[0]['title']
                self.temp.extend(total)

                return self.temp
        except IndexError:
            print("새로운 뉴스 없음")

    def start(self, interval):
        self.temp = []
        self.crawling()
        self.crawling2()
        print(self.temp)
        Timer(interval, self.start, [interval]).start()


    def cleartext(self, text):
        pat1 = re.compile('[a-zA-Z0-9]*[@].*|[ㄱ-ㅎ가-힣]{3}[\s]?기자|▶.*', re.DOTALL)
        pat2 = re.compile('\[[^\[\]]*\]|\([^\(\)]*\)|Copyrights.*|관련뉴스해당.*|<[^<>]*>|'
                          '한국경제TV|조선비즈|아시아경제|머니투데이|연합뉴스|한국경제|이데일리|매일경제|【[^【】]*】', re.DOTALL)

        text = pat1.sub("", text)
        text = pat2.sub("", text)

        return text.strip()





