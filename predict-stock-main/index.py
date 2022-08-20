# -*- coding: utf-8 -*-

from PredictFromModel import PredictFromModel;
#from RealTimeNews import RealTimeNews;
from flask import Flask, render_template, request
from realtimetweet import RealTimeTweet
from realtimenews import RealTimeNews
from operator import itemgetter
from pytz import utc
from pytz import timezone
import datetime

app = Flask(__name__)
model = PredictFromModel()

#메인 페이지
@app.route('/')
def index(query=None):
    return render_template('main.html')

# 뉴스 결과
@app.route('/result_news', methods = ['POST'])
def result_n():
    try:
        jsdata = request.form['option']
        rtn = RealTimeNews()
        now = utc.localize(datetime.datetime.utcnow()).astimezone(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")

        option=str(jsdata)

        sec = int(jsdata) * 60
        # 언론사/제목/링크/시간/내용
        data = rtn.get(sec)

        # 시간 내림차순으로 정렬
        data.sort(key=itemgetter(3), reverse=True)

        # 내용으로 예측
        if len(data) > 0:
            pred = predict([d[4] for d in data])

            newdata = []
            for d, p in zip(data, pred):
                # 0 : 언론사 (d[0])
                # 1 : 제목 (d[1])
                # 2 : 링크 (d[2])
                # 3 : 시간 (d[3])
                # 4 : 종목 (p[0])
                # 5 : 긍/부정
                # 6 : 등락
                newdata.append([d[0], d[1], d[2], d[3], p[0], f"{p[1]} ({p[2]}%)", f"{p[3]} ({p[4]}%)"])
                
            return render_template('result.html', type="news", time=now, value=option, data=newdata)
        else:
            return render_template('result.html', type="nodata")
    except Exception as e:
        print(f"result_news error : {e}")
        return render_template('result.html', type="error")

# 트위터 결과
@app.route('/result_twitter', methods = ['POST'])    
def result_t():
    try:
        keyword = request.form['keyword']

        rtt = RealTimeTweet()
        now = utc.localize(datetime.datetime.utcnow()).astimezone(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")

        # 내용/게시물id/시간
        data = rtt.get(keyword)

        # 시간 내림차순으로 정렬
        data.sort(key=itemgetter(2), reverse=True)

        # 내용으로 예측
        if len(data) > 0:
            pred = predict([d[0] for d in data])

            newdata = []
            for d, p in zip(data, pred):
                # 0 : 내용 (d[0])
                # 1 : 링크 (~~d[1])
                # 2 : 시간 (d[2])
                # 3 : 종목 (p[0])
                # 4 : 긍/부정
                # 5 : 등락
                newdata.append([d[0], f"https://twitter.com/user/status/{d[1]}", d[2], p[0], f"{p[1]} ({p[2]}%)", f"{p[3]} ({p[4]}%)"])

            return render_template('result.html', type="twitter", time=now, keyword=keyword, data=newdata)        
        else :
            return render_template('result.html', type="nodata")
    except Exception as e:
        print(f"result_twitter error : {e}")
        return render_template('result.html', type="error")


# 예측 (종목명, 긍부정, 확률, 등락, 확률)
def predict(data):
    return model.prediction(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)