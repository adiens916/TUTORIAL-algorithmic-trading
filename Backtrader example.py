# 필요한 모듈 가져오기
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'ko_KR')

import backtrader as bt


# backtrader 의 Strategy 클래스를 상속받아 분석에 필요한 지표와 로직을 구현한다.
# 5일 이동평균선과 30일 이동평균선을 지표로 사용할 예정이다.

# Create a subclass of Strategy to define the indicators and logic
class SmaCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=5,  # period for the fast moving average
        pslow=30  # period for the slow moving average
    )

    # 클래스 초기화 부분에는 두 개의 이동평균선을 이용하여 CrossOver 시그널을 만든다.
    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average

        # 0보다 크면 골든크로스, 0보다 작으면 데드크로스를 의미한다.
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal

        self.holding = 0

    # next 함수는 지정된 기간 동안 액션을 취하기 위해 순차적으로 호출되는 함수이다.
    def next(self):
        current_stock_price = self.data.close[0]

        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                # 현재의 주가를 얻어오고, 매수자의 현금 잔액을 얻어오면
                # 매수 가능한 주식의 수를 알 수 있는데, available_stocks에 그 수를 저장하였다.
                available_stocks = self.broker.getcash() / current_stock_price

                # buy 함수를 호출할 때 available_stocks 를 인자로 전달하면 전량 매수가 되겠지만
                # 예제에서는 1주씩 매수, 매도하기로 한다.
                self.buy(size=1)

        # 데드크로스의 경우에는 close 함수를 호출하여 전량 매도하도록 하였다.
        # sell 함수를 사용하면 매도하고자 하는 주식의 수를 지정할 수 있다.
        elif self.crossover < 0:  # in the market & cross to the downside
            self.close()  # close long position

    # 주문이 체결될 때 notify_order 함수가 호출되는데, 주문이 발생할 때마다
    # 매수, 매도, 주식 가격, 보유 현금, 자산 가치, 보유 주식의 수 등의 로그를 출력하도록 하였다.
    def notify_order(self, order):
        if order.status not in [order.Completed]:
            return

        if order.isbuy():
            action = 'Buy'
        elif order.issell():
            action = 'Sell'

        stock_price = self.data.close[0]
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        self.holding += order.size

        print('%s[%d] holding[%d] price[%d] cash[%.2f] value[%.2f]'
              % (action, abs(order.size), self.holding, stock_price, cash, value))


# Cerebro 엔진을 생성하고, 초기 현금과 수수료를 설정한다.
# 0.002 는 0.2% 수수료를 설정한 것을 의미한다.

cerebro = bt.Cerebro()  # create a "Cerebro" engine instance
cerebro.broker.setcash(100000)
cerebro.broker.setcommission(0.002)

# 삼성전자 주가를 사용하고, Yahoo Finance 에서 데이터를 얻어오도록 하였다.

# Create a data feed
data = bt.feeds.YahooFinanceData(dataname='MSFT',
                                 fromdate=datetime(2019, 1, 1),
                                 todate=datetime.now())

cerebro.adddata(data)  # Add the data feed

cerebro.addstrategy(SmaCross)  # Add the trading strategy

# 시뮬레이션을 실행하고 결과를 확인한다.

start_value = cerebro.broker.getvalue()
cerebro.run()  # run it all
final_value = cerebro.broker.getvalue()

print('* start value : %s won' % locale.format_string('%d', start_value, grouping=True))
print('* final value : %s won' % locale.format_string('%d', final_value, grouping=True))
print('* earning rate : %.2f %%' % ((final_value - start_value) / start_value * 100.0))

cerebro.plot()  # and plot it with a single command