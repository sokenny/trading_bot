import math
import os
import config
import sys
import io

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
fetched_candles = False
dfc = None

def backtest(bot, period, to_return="whole_log"):

    global fetched_candles
    global dfc

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    if(not fetched_candles):
        candles = bot.get_candle_sticks(config.PAIR, config.KLINE_INTERVAL, period)
        dfc = bot.get_parsed_df_w_cci(candles)
        fetched_candles = True

    for index, candle in dfc.iterrows():
        canProceed = not math.isnan(candle['CCI'])
        if(canProceed):
            CCI = candle['CCI']
            print(f'\nCCI: , {CCI} - time:  {candle["close-time"]} - bot status: ', bot.status, ' - candle price: ', candle['close'], ' - layer 1 score: ', bot.get_score(), ' - layer 2 score: ', bot.get_score(target_layer=2))

            for i, position in enumerate(bot.pending_positions):
                bot.try_open_position(i, candle)
            for i, position in enumerate(bot.open_positions):
                bot.try_close_position(i, candle)

            if(bot.status == "stalking"):
                started_regression = bot.started_regression(CCI)
                bot.last_cci = CCI
                if(started_regression):
                    print("Empezó la regresion! Abrimos compras")
                    bot.create_positions(candle['close'], candle['close-time'], CCI)
                    bot.status = "waiting"
                continue

            if(bot.reached_new_peak(CCI)):
                print("Señal disparada, esperando reversion! - Status actualizado a: stalking")
                bot.status = "stalking"
            bot.last_cci = CCI
        else:
            print('No podemos avanzar, faltan velas para calcular el CCI')

    bot.get_footer_report(print_report=True)

    sys.stdout = old_stdout
    whole_print_output = buffer.getvalue()

    return whole_print_output if to_return == "whole_log" else bot.get_footer_report(print_report=True)
