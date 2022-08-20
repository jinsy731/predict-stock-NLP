
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
from pytz import utc
from pytz import timezone
import tweepy

load_dotenv()

# .env에서 키를 가져옴
TWITTER_CONSUMER_KEY = os.getenv("twitter_consumer_key")
TWITTER_CONSUMER_SECRET = os.getenv("twitter_consumer_secret")
TWITTER_ACCESS_TOKEN = os.getenv("twitter_access_token")
TWITTER_ACCESS_SECRET = os.getenv("twitter_access_secret")

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)

api = tweepy.API(auth)

class RealTimeTweet(object):
    # 시간 포맷을 aware datetime으로 변경
    # time : 시간 (datetime)
    # 리턴 : 한국 시간, 이미 시간대가 있으면 그대로 반환
    def localize(self, time):
        try:
            t = time.astimezone(timezone('Asia/Seoul'))
        except:
            return time
        return t        

    # 키워드로 트위터 정보를 받아옴
    # api호출량 고려하여 3페이지까지만 검색
    # keyword : 키워드
    # 리턴 : 수집된 데이터 ([내용/게시물id/작성 시간] list)
    def get(self, keyword):
        result = []

        for i in range(1, 3):
            tweets = api.search(keyword)
            for tweet in tweets:
                time = utc.localize(tweet.created_at)
                # 내용, 게시물 id, 작성 시간
                result.append([tweet.text, tweet.id_str, self.localize(time).strftime("%Y-%m-%d %H:%M:%S")])
        #print(result[0])
        return result             


if __name__ == "__main__":
    rtt = RealTimeTweet()
    rtt.get("주가")