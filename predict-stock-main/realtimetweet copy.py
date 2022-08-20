import twitter # python-twitter
import json
import threading
import time

twitter_consumer_key = "uDy5FXVKLjPpPFe0qSu1OdeQK"
twitter_consumer_secret = "SLFnszXvPujPuO4eWpHc40pnB8sUeLFQ0ds4RO7GmttcVzsOiF"
twitter_access_token = "1382357822814310407-PVASZzkZjBKZBsiGoOWzPHTBHjpuOt"
twitter_access_secret = "qVSdFUBs4U4UuINRRXlOBFK6HOtrKg7A55P2TUewBrIam"
flag = 0

class RealTimeTweet(object):
    def __init__(self):
        self.twitter_api = twitter.Api(consumer_key = twitter_consumer_key,
        consumer_secret = twitter_consumer_secret,
        access_token_key = twitter_access_token,
        access_token_secret = twitter_access_secret)
        self.flag = 0
        
    def start(self, query, time=10):
        # 플래그 설정
        self.flag = 0
        # 출력 파일
        output_file_name = "stream_result.txt"
        # 출력 내용
        output = []

        # 출력 파일에 내용 작성
        with open(output_file_name, "w", encoding="utf-8") as output_file:
            stream = self.twitter_api.GetStreamFilter(track = query)
            while self.flag == 0:
                print("while")
                threading.Timer(time, self.stop).start()       
                for tweets in stream:
                    tweet = json.dumps(tweets, ensure_ascii=False)
                    print(tweet, file=output_file, flush=True)
                    output.append(json.loads(tweet)["text"])
                    #print(json.loads(tweet)["text"])
                    if self.flag == 1:
                        return output
             

    def stop(self):
        print("self.stop")
        self.flag = 1

    def readjson(self):
        d = []
        with open("stream_result.txt", "r", encoding="utf-8", newline="") as json_data:
            while True:
                line = json_data.readline()
                if not line: break
                j = json.loads(line)
                d.append(j["text"])
                #print(j["text"])
        return d

    def test(self):
        input_file_name = "stream_result.txt"
        output_file_name = "stream_result2.txt"

        with open(input_file_name, "r", encoding="utf-8", newline="") as input_file, \
            open(output_file_name, "w", encoding="utf-8", newline="") as output_file:

            while True:
                line = input_file.readline()
                if not line: break
                j = json.loads(line)
                #print(j["text"])
                output_file.write(j["text"])

if __name__ == "__main__":
    rtt = RealTimeTweet()
    #rtt.start(["코로나"])
    #rtt.readjson()
    rtt.test()
