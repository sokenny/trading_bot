import math
import os
import config
import sys
import io
from Bot import Bot as BotClass

THIS_PATH = os.path.abspath(os.path.dirname(__file__))

def backtest(__PAIR=config.PAIR, __PERIOD=config.PERIOD, __TRADE_AMOUNT=config.TRADE_AMOUNT, __TAKER_PROFIT=config.TAKER_PROFIT, __STOP_LOSS=config.STOP_LOSS, __POSITIONS_STRUCTURE=config.POSITIONS_STRUCTURE, __KLINE_TO_USE_IN_PROD=config.KLINE_TO_USE_IN_PROD, __KLINE_INTERVAL=config.KLINE_INTERVAL, __CCI_PEAK=config.CCI_PEAK, __POSITION_EXPIRY_TIME=config.POSITION_EXPIRY_TIME, __SCORE_FILTER=config.SCORE_FILTER, __SCORE_LONGITUDE=config.SCORE_LONGITUDE, __START_GAP_PERCENTAGE=config.START_GAP_PERCENTAGE):

    old_stdout = sys.stdout  # Memorize the default stdout stream
    sys.stdout = buffer = io.StringIO()

    Bot = BotClass("sandbox", __PAIR, __TRADE_AMOUNT, __TAKER_PROFIT, __STOP_LOSS,  __POSITIONS_STRUCTURE, __KLINE_TO_USE_IN_PROD, __KLINE_INTERVAL, __CCI_PEAK, __POSITION_EXPIRY_TIME, __SCORE_FILTER, __SCORE_LONGITUDE, __START_GAP_PERCENTAGE)
    candles = Bot.get_candle_sticks(config.PAIR, config.KLINE_INTERVAL, __PERIOD)
    dfc = Bot.get_parsed_df_w_cci(candles)

    for index, candle in dfc.iterrows():
        canProceed = not math.isnan(candle['CCI'])
        if(canProceed):
            CCI = candle['CCI']
            print(f'\nCCI: , {CCI} - time:  {candle["close-time"]} - bot status: ', Bot.status, ' - candle price: ', candle['close'], ' - layer 1 score: ', Bot.get_score(), ' - layer 2 score: ', Bot.get_score(target_layer=2))

            for i, position in enumerate(Bot.pending_positions):
                Bot.try_open_position(i, candle)
            for i, position in enumerate(Bot.open_positions):
                Bot.try_close_position(i, candle)

            if(Bot.status == "stalking"):
                started_regression = Bot.started_regression(CCI)
                Bot.last_cci = CCI
                if(started_regression):
                    print("Empezó la regresion! Abrimos compras")
                    Bot.create_positions(candle['close'], candle['close-time'], CCI)
                    Bot.status = "waiting"
                continue

            if(Bot.reached_new_peak(CCI)):
                print("Señal disparada, esperando reversion! - Status actualizado a: stalking")
                Bot.status = "stalking"
            Bot.last_cci = CCI
        else:
            print('No podemos avanzar, faltan velas para calcular el CCI')

    Bot.get_footer_report(print_report=True)

    sys.stdout = old_stdout
    whole_print_output = buffer.getvalue()

    return whole_print_output
