import math
import os
import config
from utils import Bot

THIS_PATH = os.path.abspath(os.path.dirname(__file__))

Ant = Bot("sandbox", config.PAIR, config.TRADE_AMOUNT, config.TAKER_PROFIT, config.STOP_LOSS, config.POSITIONS_STRUCTURE, config.KLINE_TO_USE_IN_PROD, config.KLINE_INTERVAL, config.CCI_PEAK, config.POSITION_EXPIRY_TIME)

candles = Ant.get_candle_sticks(config.PAIR, config.KLINE_INTERVAL, config.PERIOD)

dfc = Ant.get_parsed_df_w_cci(candles)

for index, candle in dfc.iterrows():
    canProceed = not math.isnan(candle['CCI'])
    if(canProceed):
        CCI = candle['CCI']
        print('\nCCI: ', CCI, ', time: ', candle['close-time'], ' - bot status: ', Ant.status, ' - candle price: ', candle['close'])

        for i, position in enumerate(Ant.pending_positions):
            Ant.try_open_position(i, candle)
        for i, position in enumerate(Ant.open_positions):
            Ant.try_close_position(i, candle)

        if(Ant.status == "stalking"):
            started_regression = Ant.started_regression(CCI)
            Ant.last_cci = CCI
            if(started_regression):
                print("Empezó la regresion! Abrimos compras")
                Ant.create_positions(candle['close'], candle['close-time'], CCI)
                Ant.status = "waiting"
            continue

        if(Ant.reached_new_peak(CCI)):
            print("Señal disparada, esperando reversion! - Status actualizado a: stalking")
            Ant.status = "stalking"
        Ant.last_cci = CCI
    else:
        print('No podemos avanzar, faltan velas para calcular el CCI')

won = 0
won_weights = 0
lost = 0
lost_weights = 0

for pos in Ant.closed_positions:
    if(pos['outcome'] == 1):
        won += 1
        won_weights += pos['weight']
    else:
        lost += 1
        lost_weights += pos['weight']

print(Ant.closed_positions)
print('Won: ', won, ' - Won weights: ', won_weights)
print('Lost: ', lost, ' - Lost weights: ', lost_weights)
print('score: ', Ant.get_score())

# for index, candle in dfc.iterrows():
#     print(candle)