import math
import os
import config
from utils import Bot

import sys
import io

THIS_PATH = os.path.abspath(os.path.dirname(__file__))

def backtest(__PAIR=config.PAIR, __PERIOD=config.PERIOD, __TRADE_AMOUNT=config.TRADE_AMOUNT, __TAKER_PROFIT=config.TAKER_PROFIT, __STOP_LOSS=config.STOP_LOSS, __POSITIONS_STRUCTURE=config.POSITIONS_STRUCTURE, __KLINE_TO_USE_IN_PROD=config.KLINE_TO_USE_IN_PROD, __KLINE_INTERVAL=config.KLINE_INTERVAL, __CCI_PEAK=config.CCI_PEAK, __POSITION_EXPIRY_TIME=config.POSITION_EXPIRY_TIME, __SCORE_FILTER=config.SCORE_FILTER, __SCORE_LONGITUDE=config.SCORE_LONGITUDE, __START_GAP_PERCENTAGE=config.START_GAP_PERCENTAGE):

    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()

    Ant = Bot("sandbox", __PAIR, __TRADE_AMOUNT, __TAKER_PROFIT, __STOP_LOSS,  __POSITIONS_STRUCTURE, __KLINE_TO_USE_IN_PROD, __KLINE_INTERVAL, __CCI_PEAK, __POSITION_EXPIRY_TIME, __SCORE_FILTER, __SCORE_LONGITUDE, __START_GAP_PERCENTAGE)
    candles = Ant.get_candle_sticks(config.PAIR, config.KLINE_INTERVAL, __PERIOD)
    dfc = Ant.get_parsed_df_w_cci(candles)

    for index, candle in dfc.iterrows():
        canProceed = not math.isnan(candle['CCI'])
        if(canProceed):
            CCI = candle['CCI']
            print(f'\nCCI: , {CCI} - time:  candle["close-time"] - bot status: ', Ant.status, ' - candle price: ', candle['close'], ' - layer 1 score: ', Ant.get_score(), ' - layer 2 score: ', Ant.get_score(target_layer=2))

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

    print('\nCLOSED POSITIONS: ')
    print(Ant.closed_positions)
    print('\nWon: ', won, ' - Won weights: ', won_weights)
    print('Lost: ', lost, ' - Lost weights: ', lost_weights)
    print("Positions left open: ", len(Ant.open_positions))
    print('Layer 1 score: ', Ant.get_score())
    print("Layer 2 score: ", Ant.get_score(target_layer=2))
    print("\n CONFIG USED: ")
    print(Ant.get_config())

    sys.stdout = old_stdout  # Put the old stream back in place
    whole_print_output = buffer.getvalue()
    return whole_print_output
