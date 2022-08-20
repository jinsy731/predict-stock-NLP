from transformers import ElectraTokenizer, TFElectraForSequenceClassification
from tensorflow.keras.layers import Softmax
import tensorflow as tf
import pandas as pd
import re
import numpy as np

class PredictFromModel(object):

    def __init__(self):
        self.MAX_LEN = 512
        self.tokenizer = ElectraTokenizer.from_pretrained("monologg/koelectra-base-v3-discriminator")
        self.cls_model = TFElectraForSequenceClassification.from_pretrained('monologg/koelectra-base-v3-discriminator', from_pt=True)
        #self.cls_model1 = TFElectraForSequenceClassification.from_pretrained('monologg/koelectra-base-v3-discriminator', from_pt=True)
        self.cls_model2 = TFElectraForSequenceClassification.from_pretrained('monologg/koelectra-base-v3-discriminator', from_pt=True)

        optimizer = tf.keras.optimizers.Adam(3e-5)
        loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        metric = tf.keras.metrics.SparseCategoricalAccuracy('accuracy')

        self.cls_model.compile(optimizer=optimizer, loss=loss, metrics=[metric])  # 주가 등락 분류 모델
        #self.cls_model1.compile(optimizer=optimizer, loss=loss, metrics=[metric])  # 뉴스 긍/부정 분류 모델
        self.cls_model2.compile(optimizer=optimizer, loss=loss, metrics=[metric])  # 뉴스 긍/부정 분류 모델

        #self.cls_model1.load_weights('./weights_h5/weights.h5')
        self.cls_model2.load_weights('./weights_h5/weights2.h5')
        self.cls_model.load_weights('./weights_h5/weights3.h5')

        self.corp_name_df = pd.read_csv('./stock_name.csv', index_col=0)

        self.two_word_corp = ['CJ CGV', 'CJ ENM', 'CJ제일제당 우', 'CSA 코스믹', 'JYP Ent.', 'KG ETS', 'KH E&T', 'KH 일렉트론', 'KH 필룩스',
                         'LS ELECTRIC', 'SM C&C', 'SM Life Design', 'THE E&M', 'THE MIDONG', 'YG PLUS', '리더스 기술투자',
                         '미래에셋대우스팩 5호', '블루베리 NFT', '비보존 헬스케어', '신세계 I&C', '에이프로젠 H&G', '에이프로젠 KIC', '포스코 ICT']

        self.acronym = {'SK바사': 'SK바이오사이언스', '네이버': 'NAVER', 'SKIET': 'SK아이이테크놀로지', '진원생명': '진원생명과학',
                   '삼성바이오': '삼성바이오로직스', '삼바': '삼성바이오로직스', 'RF머트': 'RF머트리얼즈', '기아차': '기아', 'SKT': 'SK텔레콤',
                   '두산인프라': '두산인프라코어', '한국타이어': '한국타이어앤테크놀로지', '하이마트': '롯데하이마트', 'LGD': 'LG디스플레이',
                   '하이닉스': 'SK하이닉스', '포스코': 'POSCO', '현대차그룹': '현대차', '현대자동차': '현대차', 'OCI머티리얼즈': 'OCI',
                   '네오위즈게임즈': '네오위즈',
                   '소마젠': '소마젠(Reg.S)', 'JYP엔터': 'JYP Ent.', '뉴지랩': '뉴지랩파마', 'YG엔터': '와이지엔터테인먼트', '포스코ICT': '포스코 ICT',
                   '삼성SDS': '삼성에스디에스', 'KAI': '한국항공우주', '동부제철': 'KG동부제철', '초록뱀': '초록뱀미디어', '현대중공업': '현대중공업지주',
                   '한화케미칼': '한화솔루션', 'NHN엔터테인먼트': 'NHN', 'NHN엔터': 'NHN', 'LS산전': 'LS ELECTRIC'}

    def bert_tokenizer(self, sent, MAX_LEN):
        pat = re.compile('[-.:\'\"=]')
        sent = pat.sub(" ", sent)
        sent = sent.strip()

        encoded_dict = self.tokenizer.encode_plus(
            text=sent,
            add_special_tokens=True,  # Add '[CLS]' and '[SEP]'
            max_length=MAX_LEN,  # Pad & truncate all sentences.
            pad_to_max_length=True,
            return_attention_mask=True  # Construct attn. masks.

        )

        input_id = encoded_dict['input_ids']
        attention_mask = encoded_dict[
            'attention_mask']  # And its attention mask (simply differentiates padding from non-padding).
        token_type_id = encoded_dict['token_type_ids']  # differentiate two sentences

        return input_id, attention_mask, token_type_id


    def extract_corpname(self, text):
        pat = re.compile('\[[^\[\]]*\]|\([^\(\)]*\)|[,.\"\'`를은는을]')
        title = pat.sub("", text)
        title_tkn = title.split(" ")
        disc_corp_name = []

        for corp_name in self.corp_name_df.values:
            corp_name = corp_name[0]
            if corp_name in self.two_word_corp:
                split_name = corp_name.split(" ")
                if all([name_tkn in title_tkn for name_tkn in split_name]):
                    disc_corp_name.append(corp_name)
            elif corp_name in title_tkn:
                disc_corp_name.append(corp_name)
            elif any([self.acronym.get(token) == corp_name for token in title_tkn]):
                disc_corp_name.append(corp_name)

        if len(disc_corp_name) == 0:
            result = None
        elif len(disc_corp_name) > 1:
            result = disc_corp_name[0]
        else:
            result = disc_corp_name[0]

        return result

    # 변경점
    # 결과 프린트 -> 결과값 리턴
    # 리턴 : [종목명, 긍/부정, 긍부정확률, 등락, 등락확률] 리스트
    def prediction(self, text_set):

        input_ids = []
        attention_masks = []
        token_type_ids = []

        for text in text_set:
            try:
                #print(text)
                input_id, attention_mask, token_type_id = self.bert_tokenizer(text, self.MAX_LEN)
                input_ids.append(input_id)
                attention_masks.append(attention_mask)
                token_type_ids.append(token_type_id)
            except Exception as e:
                print(e)
                print(text)
                pass

        # train_input_ids.append(input_ids)로 리스트에 다시 batch의 input_ids를 넣을 때와 달리(학습시) 지금은 하나의 데이터만 사용하므로 리스트 안에 input_ids를 직접 넣어서 model의 인풋으로 넣어줘야함.
        input_ids = np.array(input_ids, dtype=int)
        attention_masks = np.array(attention_masks, dtype=int)
        token_type_ids = np.array(token_type_ids, dtype=int)

        # encoded = {'input_ids': input_ids, 'attention_masks': attention_masks, 'token_type_ids': token_type_ids}
        inputs = (input_ids, attention_masks, token_type_ids)

        layer = Softmax()

        #results1 = layer(self.cls_model1.predict(inputs)[0])  # 긍/부정 분류 결과
        results2 = layer(self.cls_model2.predict(inputs)[0])  # 주가 등락 여부 분류 결과
        results3 = layer(self.cls_model.predict(inputs)[0])

        r = []

        #for text, result1, result2, result3 in zip(text_set, results1, results2, results3):
        for text, result2, result3 in zip(text_set, results2, results3):

            corp_name = self.extract_corpname(text)

            arg = np.argmax(result2.numpy().flatten())
            if arg == 0:
                pn = '부정'
            else:
                pn = '긍정'
            prob_pn = np.round(result2.numpy().flatten()[arg] * 100, 2)

            arg = np.argmax(result3.numpy().flatten())
            if arg == 0:
                ud = '하락'
            else:
                ud = '상승'
            prob_ud = np.round(result3.numpy().flatten()[arg] * 100, 2)

            r.append([corp_name, pn, prob_pn, ud, prob_ud])

        return r




