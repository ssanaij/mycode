#!/usr/local/bin/python3

import time
import pyupbit
import datetime
import schedule
from fbprophet import Prophet
import decimal


# 변수 선언
access = "U9kcbBExlwCxevY5hVfsxYH633p5xDogcUqoC5Sl"
secret = "A5zzKBZxNVv9hMVcM86ztdLqfMxc5GfHoP47xVqw"

coin_name = "KRW-BTC"
buy_price = 5100

# 함수시작

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2) # 240분봉(4시간, 하루 6번)이 제일 큼 09,13,17,21,01,05,09
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return decimal.Decimal(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

predicted_close_price = 0
def predict_price(ticker):
    """Prophet으로 4시간 종가 가격 예측"""
    global predicted_close_price
    df = pyupbit.get_ohlcv(ticker, interval="minute60")
    #print(df)
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    model = Prophet()
    model.fit(data)
    future = model.make_future_dataframe(periods=4, freq='H')
    forecast = model.predict(future)
    #print(forecast)
    #closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds'].replace(hour=9)]
    closeDf = forecast[forecast['ds'] == forecast.iloc[-1]['ds']]
    if len(closeDf) == 0:
        #closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds'].replace(hour=9)]
        closeDf = forecast[forecast['ds'] == data.iloc[-1]['ds']]
    closeValue = closeDf['yhat'].values[0]
    predicted_close_price = closeValue

# 함수 끝

predict_price(coin_name)
#schedule.every().hour.do(lambda: predict_price(coin_name))
schedule.every().minute.do(lambda: predict_price(coin_name))

# 로그인
upbit = pyupbit.Upbit(access, secret)
blended_price = 0
balance = 0
buy = {}
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(coin_name)
        end_time = start_time + datetime.timedelta(hours=4)
        current_price = get_current_price(coin_name)
        schedule.run_pending()

        if start_time < now < end_time - datetime.timedelta(seconds=10):
        #if False: # for debug
            target_price = get_target_price(coin_name, 0.5)
            date_time = now.strftime("%m/%d/%Y %H:%M:%S")
            #로그 출력
            print( date_time + ", 예측 : " + str(predicted_close_price) + ", 목표 : " + str(target_price) + ", 현재 : " + str(current_price))

            if target_price < current_price and current_price < predicted_close_price:
            #if True: # for debug
                #krw = get_balance("KRW")
                krw = buy_price # 사전 정의한 구매 금액으로 구매함
                if krw > 5000 and buy == {} : #여러번 구매해서 한번만 구매 하도록 수정
                    buy = upbit.buy_market_order(coin_name, krw*0.9995) # 샀을때 구매 가격 구매 갯수 확인

                    # buy sample
                    #{'uuid': 'fac442e9-a644-43e8-a166-00b0c430cc8a', 'side': 'bid',
                    # 'ord_type': 'price', 'price': '5010.0', 'state': 'wait', 'market': 'KRW-BTT',
                    # 'created_at': '2021-04-22T17:22:33+09:00', 'volume': None,
                    # 'remaining_volume': None, 'reserved_fee': '2.505', 'remaining_fee': '2.505',
                    # 'paid_fee': '0.0', 'locked': '5012.505', 'executed_volume': '0.0',
                    # 'trades_count': 0}
                    print(buy)

                    if blended_price == 0: # 매수평균이 0 = 최초구매
                        blended_price = buy['price']
                    else: # 매수평균이 0이 아니면 여러번 안팔았다는 뜻
                        blended_price = ( blended_price + buy['price'] ) / 2

        else: # 사전 설정한 시간이 다 지나서 팔아야 할 시간
            coin2krw = upbit.get_balances()
            #print(coin2krw[1]['currency'])
            for key in coin2krw:
                if key['currency'] == coin_name[4:]:
                    coin2krw_now = decimal.Decimal(key['avg_buy_price']) * decimal.Decimal(key['balance']) # 현재 코인 구매 평균가 x 현재 코인 개수
                    balance = decimal.Decimal(key['balance']) # 코인갯수
                    #print(str(coin2krw_now)) # 현재 코인의 원화 가치

            if coin2krw_now > 5000 and current_price > blended_price and blended_price > 0 : # 가지고 있는 코인이 원화 5천원 이상이면 판매, 매수평균가 보다 현재 가격이 높아야 함
                sell = upbit.sell_market_order(coin_name, balance * decimal.Decimal(0.9995)) # 팔때 총 갯수와 구매 평균가격 확인
                print(sell)
                blended_price = 0

        time.sleep(1)
    except Exception as e:
        print(e) # 에러나면 에러 프린트
        time.sleep(1)
