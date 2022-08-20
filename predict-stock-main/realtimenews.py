# -*- coding: utf-8 -*-

import csv
import datetime
import requests
import re
import threading
from bs4 import BeautifulSoup as bs
from pytz import utc
from pytz import timezone

class RealTimeNews(object):
    def __init__(self):
        # 각 언론사별 정보
        # name : 언론사 이름
        # link : 해당 rss 링크
        # pubDateTag : 기사 작성시간 태그 이름
        # timeFormat : 기사 작성시간 포맷
        # contentTag : 기사 페이지에서의 기사 내용 태그 이름
        # contentProp : 기사 페이지에서의 기사 내용 태그의 옵션

        self.urls = [
            {"name":"SBS뉴스 (경제)", "link":"https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=02&plink=RSSREADER", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"경향신문 (경제)", "link":"http://www.khan.co.kr/rss/rssdata/economy_news.xml", "pubDateTag":"dc:date", "timeFormat":"%Y-%m-%dT%H:%M:%S%z"},
            {"name":"뉴시스 (경제)", "link":"https://newsis.com/RSS/economy.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"동아일보 (경제)", "link":"https://rss.donga.com/economy.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"매일경제 (경제)", "link":"https://www.mk.co.kr/rss/30100041/", "pubDateTag":"pubDate", "timeFormat":"%Y-%m-%dT%H:%M:%S%z"},
            {"name":"매일경제 (증권)", "link":"https://www.mk.co.kr/rss/50200011/", "pubDateTag":"pubDate", "timeFormat":"%Y-%m-%dT%H:%M:%S%z"},
            {"name":"세계일보 (경제)", "link":"http://www.segye.com/Articles/RSSList/segye_economy.xml", "pubDateTag":"pubDate", "timeFormat":"%a,%d %b %Y %H:%M:%S %z"},
            {"name":"연합뉴스 (경제)", "link":"http://www.yonhapnewstv.co.kr/category/news/economy/feed/", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"이데일리 (주식/펀드)", "link":"http://rss.edaily.co.kr/stock_news.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"이데일리 (경제/정책)", "link":"http://rss.edaily.co.kr/economy_news.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"이데일리 (금융/M&A)", "link":"http://rss.edaily.co.kr/finance_news.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"이데일리 (채권/외환)", "link":"http://rss.edaily.co.kr/bondfx_news.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"이데일리 (기업)", "link":"http://rss.edaily.co.kr/enterprise_news.xml", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"},
            {"name":"중앙일보 (경제)", "link":"https://rss.joins.com/joins_money_list.xml", "pubDateTag":"pubDate", "timeFormat":"%Y-%m-%dT%H:%M:%S%z"},
            {"name":"파이낸셜뉴스 (경제)", "link":"https://www.fnnews.com/rss/r20/fn_realnews_economy.xml", "pubDateTag":"pubDate", "timeFormat":"%a,%d %b %Y %H:%M:%S %z"},
            {"name":"파이낸셜뉴스 (증권)", "link":"https://www.fnnews.com/rss/r20/fn_realnews_stock.xml", "pubDateTag":"pubDate", "timeFormat":"%a,%d %b %Y %H:%M:%S %z"},
            {"name":"파이낸셜뉴스 (금융)", "link":"https://www.fnnews.com/rss/r20/fn_realnews_finance.xml", "pubDateTag":"pubDate", "timeFormat":"%a,%d %b %Y %H:%M:%S %z"},
            {"name":"프레시안 (경제)", "link":"http://www.pressian.com/api/v3/site/rss/section/67", "pubDateTag":"dc:date", "timeFormat":"%Y-%m-%d %H:%M:%S"},
            {"name":"헤럴드경제 (재테크))", "link":"http://biz.heraldcorp.com/common/rss_xml.php?ct=4", "pubDateTag":"pubDate", "timeFormat":"%a, %d %b %Y %H:%M:%S %z"}
        ]

        self.flag = 0
    
    # 링크로부터 기사 내용을 가져옴
    # link : 기사의 링크
    # contentTag : 내용이 담긴 태그 이름
    # contentProp : 해당 태그의 옵션
    # 리턴 : 태그가 포함된 기사의 내용 부분
    def getContentsFromLink(self, link):
        headers = {"User-Agent":"Mozilla/5.0"}
        articlePage = requests.get(link, headers=headers)
        article = bs(articlePage.content, "html.parser", from_encoding="utf-8")

        contents = article.find("div", {"itemprop":"articleBody"})

        if not contents == None:
            return contents

        # 파이낸셜
        contents = article.find("div", {"id":"article_content"})
        if not contents == None:
            return contents

        # 일부 경향신문
        contents = article.find("p", {"class":"art_text"})
        if not contents == None:
            contents = list(map(str, article.find_all("p", {"class":"art_text"})))
            contents = "".join(contents)
            return contents

        return None

    # 시간 포맷을 aware datetime으로 변경
    # time : 시간 (datetime)
    # 리턴 : 한국 시간, 이미 시간대가 있으면 그대로 반환
    def localize(self, time):
        try:
            t = time.astimezone(timezone('Asia/Seoul'))
        except:
            return time
        return t

    # 불필요한 태그 제거
    # text : 태그를 제거할 내용
    # 리턴 : 태그가 제거된 내용
    def removeTag(self, text):
        # 불필요 태그 안 내용까지 제거
        contents = re.sub("<!--.*?-->|<a.*?>.*?</a>|<button.*?>.*?</button>|<em.*?>.*?</em>|<figure.*?>.*?</figure>|<figcaption.*?>.*?</figcaption>|<script.*?>.*?</script>|<span.*?>.*?</span>|<table.*?>.*?</table>", "", str(text), 0, re.I|re.S)

        # 특정 div태그 제거
        # 경향신문 소제목 <p class=[^>]+content_text[^<]+><strong>.*?</strong>.*?</p>|<p class=[^>]+content_text[^<]+><b>.*?</b>.*?</p>|<p class=[^>]+content_text[^<]+><b class=[^>]+strapline[^<]+>.*?</b>.*?</p>
        # 경향신문 사진 설명 <div class=[^>]+art_photo.*?>.*?</div>
        # 경향신문 광고 <div class=[^>]+boxLineBG.*?>.*?</div>
        # 뉴시스 소제목 <div class=[^>]+summary_view.*?>.*?</div>
        # 동아일보 추천기사 <div id=[^>]+bestnews_layer.*?>.*?</div>
        # 매일경제 이미지 설명 <div class=[^>]+img_center.*?>.*?</div>
        # 중앙일보 부제목 <div class=[^>]+ab_subtitle.*?>.*?</div>
        # 중앙일보 소제목 <div class=[^>]+ab_sub_heading.*?>.*?</div>
        # 중앙일보 연관기사 <div class=[^>]+ab_related_article.*?>.*?</div>
        # 중앙일보 사진 설명 <div class=[^>]+ab_photo.*?>.*?</div>
        # 파이넨셜 부제목 <div class=[^>]+art_subtit.*?>.*?</div>
        # 파이넨셜 저작권 <p class=[^>]+art_copyright.*?>.*?</p>
        # 헤럴드경제 소제목 <div class=[^>]+summary_area.*?>.*?</div>

        # content text는 경향이면 지우면 안됨 ? 근데 소제목도 그거네
        contents = re.sub("<p class=[^>]+content_text[^<]+><strong>.*?</strong>.*?</p>|<p class=[^>]+content_text[^<]+><b>.*?</b>.*?</p>|<p class=[^>]+content_text[^<]+><b class=[^>]+strapline[^<]+>.*?</b>.*?</p>|<div class=[^>]+art_photo.*?>.*?</div>|<div class=[^>]+boxLineBG.*?>.*?</div>|<div class=[^>]+summary_view.*?>.*?</div>|<div id=[^>]+bestnews_layer.*?>.*?</div>|<div class=[^>]+img_center.*?>.*?</div>|<div class=[^>]+ab_subtitle.*?>.*?</div>|<div class=[^>]+ab_sub_heading.*?>.*?</div>|<div class=[^>]+ab_related_article.*?>.*?</div>|<div class=[^>]+ab_photo.*?>.*?</div>|<div class=[^>]+art_subtit.*?>.*?</div>|<p class=[^>]+art_copyright.*?>.*?</p>|<div class=[^>]+summary_area.*?>.*?</div>", "", contents, 0, re.I|re.S)

        # 태그만 제거, 공백 제거
        contents = re.sub("<.*?>", "", contents, 0, re.I|re.S).strip()        
        return contents

    # (기사 내용에서) 불필요한 내용 제거
    # text : 기사 내용
    # 리턴 : 불필요한 내용이 제거된 텍스트
    def edit(self, text):
        # <앵커>, <기자> 등
        # (영상출처 홍길동), (홍길동 기상캐스터) 등
        sbs = re.sub("&lt;.*?&gt;|\([^\)]+[영상|화면|사진|구성|편집|기상|SBS].*?\)", "", text, 0, re.I|re.S)

        # [서울=뉴시스] 홍길동 기자 = 
        # 뉴시스 마지막 내용
        nss = re.sub("[가-힣 ]+ 기자 = |◎공감언론.*?com", "", sbs, 0, re.I|re.S)

        # (서울=뉴스1)
        # 서울=홍길동 기자 email
        # 동아닷컴 수식어 홍길동 기자 email
        # 홍길동 동아닷컴 ~~기자 email
        # 홍길동 ~~기자 email
        # 서울=홍길동 특파원 email
        # 홍길동 온라인 뉴스 기자 email
        da = re.sub("\([가-힣]+=뉴스1\)|[가-힣]+=[가-힣]+ 기자 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|동아닷컴 [\w ]* 기자 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|[가-힣]+ 동아닷컴 [\w]*기자 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|[가-힣]+ [\w]*기자 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|[가-힣]+=[가-힣]+ 특파원 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|[가-힣]+ 온라인 뉴스 기자 [0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}", "", nss, 0, re.I|re.S)

        # , 사진=~~뉴스
        sg = re.sub("(, )?사진=[\w ]+\n", "", da, 0, re.I|re.S)

        # 연합뉴스TV ~입니다. 연합뉴스V 제보 ~~ (끝)
        yh = re.sub("연합뉴스TV.*?(끝)", "", sg, 0, re.I|re.S)

        # 이메일, 기타 괄호 제거
        em = re.sub("[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}|\[.*?\]|【.*?】", "", yh, 0, re.I|re.S)
        return em

    # 기사들을 불러와 csv파일 작성
    # delta : 현재 시간으로부터 기사 시간 간격 제한 
    def writeCSV(self, delta):
        d = datetime.timedelta(seconds=delta)
        now = utc.localize(datetime.datetime.utcnow())
        filename = (now + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H-%M-%S")

        with open("news_data/" + filename + ".csv", "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            # headers = {"User-Agent":"Mozilla/5.0"}

            # 각 언론사별로 진행
            for url in self.urls:
                # 언론사 이름 출력
                print('--- ' + url["name"] + ' ---')
                try:
                    page = requests.get(url["link"])
                    soup = bs(page.content, 'lxml-xml')
                    elements = soup.find_all('item')
                except:
                    print("페이지 불러오기 오류")
                    continue

                # 각 기사별 진행
                for element in elements:
                    title = element.title.text
                    link = element.link.text
                    pubdate = self.localize(datetime.datetime.strptime(element.find(url["pubDateTag"]).text, url["timeFormat"]))

                    # 지정된 시간보다 오래된 기사일 경우 내림차순이므로 바로 break
                    if now - d >= pubdate:
                        break

                    # 작성 시간 포맷 통일
                    pubdate = pubdate.strftime("%Y-%m-%d %H-%M-%S")

                    contents = str(self.getContentsFromLink(link))

                    contents = str(self.removeTag(contents))

                    ## csv 읽기를 위해 ,와 줄바꿈 제거
                    #contents = re.sub(",|\r|\n", "", contents, 0, re.I|re.S)

                    # 불필요 내용 제거
                    contents = self.edit(contents)

                    ## csv 읽기를 위해 ,와 줄바꿈 제거
                    #title = re.sub(",|\r|\n", "", title, 0, re.I|re.S)

                    # csv 파일 내용 작성
                    writer.writerow([url["name"], title, link, pubdate, contents])
                    print("작성 완료 : " + title)

                    # 테스트용 (언론사별 최대 1개만 작성)
                    #break

    # 일정 시간마다 자동 수집 시작
    # seconds : 주기 (초)
    def start(self, seconds):
        self.flag = 1
        self.loop(seconds)

    # start 시 루프가 진행되는 구간
    # seconds : 주기 (초)
    def loop(self, seconds):
        if self.flag == 0:
            return
        self.writeCSV(seconds)
        if self.flag == 1:
            threading.Timer(seconds, self.loop, [seconds]).start()

    # start로 시작된 루프를 멈춤
    def stop(self):
        self.flag = 0

    # 웹에서 정보를 가져오기 위한 메소드
    # delta : 현재 시간으로부터 기사 시간 간격 제한
    def get(self, delta):
        data = []

        d = datetime.timedelta(seconds=delta)
        now = utc.localize(datetime.datetime.utcnow())
        # 각 언론사별로 진행
        for url in self.urls:
            # 언론사 이름 출력
            print('--- ' + url["name"] + ' ---')
            try:
                page = requests.get(url["link"])
                soup = bs(page.content, 'lxml-xml')
                elements = soup.find_all('item')
            except Exception as e:
                print(f"페이지 불러오기 오류 : {e}")
                continue

            # 각 기사별 진행
            for element in elements:
                title = element.title.text
                link = element.link.text
                pubdate = self.localize(datetime.datetime.strptime(element.find(url["pubDateTag"]).text, url["timeFormat"]))

                # 지정된 시간보다 오래된 기사일 경우 내림차순이므로 바로 break
                if now - d >= pubdate:
                    break

                # 작성 시간 포맷 통일
                pubdate = pubdate.strftime("%Y-%m-%d %H:%M:%S")

                contents = str(self.getContentsFromLink(link))

                contents = str(self.removeTag(contents))

                # 불필요 내용 제거
                contents = self.edit(contents)

                data.append([url["name"], title, link, pubdate, contents])
                print(f"데이터 추가됨 : {title}")

        return data

if __name__ == "__main__":
    #test = "http://news.khan.co.kr/kh_news/khan_art_view.html?artid=202106010600005&code=940702&utm_campaign=rss_btn_click&utm_source=khan_rss&utm_medium=rss&utm_content=total_news"
    #test2 = """<p class=\"content_text\">제거하면안됨</p><p class=\"content_text\"><strong>제거해야됨</strong></p><p class=\"content_text\"><b>제거해야됨2</b></p><p class=\"content_text\"><b class=\"strapline\">제거해야됨3</b></p>"""
    #result = re.sub("<p class=[^>]+content_text.*?>[<strong>.*?</strong>|<b class=[^>]+strapline.*?>.*?</b>|<b>.*?</b>].*?</p>", "", test2, 0, re.I|re.S)
    #result = re.sub("<p class=[^>]+content_text[^<]+><strong>.*?</strong>.*?</p>|<p class=[^>]+content_text[^<]+><b>.*?</b>.*?</p>|<p class=[^>]+content_text[^<]+><b class=[^>]+strapline[^<]+>.*?</b>.*?</p>", "", test2, 0, re.I|re.S)
    #result = re.sub("<p", "", test2, 0, re.I|re.S)
    rtn = RealTimeNews()
    #result = rtn.edit(rtn.removeTag(rtn.getContentsFromLink(test)))
    #print(rtn.getContentsFromLink(test))
    #result = rtn.removeTag(test2)
    #print(result)
    
    rtn.start(600)
