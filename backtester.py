import math
import sys
import io

def backtest(bot, candles):

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    dfc = bot.get_parsed_df_w_cci(candles)

    for index, candle in dfc.iterrows():
        bot.last_candle = candle
        canProceed = not math.isnan(candle['CCI'])
        if(canProceed):
            trade_over_candle(bot, candle)
        else:
            print('No podemos avanzar, faltan velas para calcular el CCI')

    print("\nTRADING ENDED.")
    bot.get_footer_report(print_report=True)
    sys.stdout = old_stdout
    whole_print_output = buffer.getvalue()

    return [whole_print_output, bot.get_footer_report(print_report=True)]

def trade_over_candle(bot, candle):
    CCI = candle['CCI']
    print(f'\nCCI: , {CCI} - time:  {candle["close-time"]} - bot status: ', bot.status, ' - candle price: ',
          candle['close'], ' - score: ', bot.get_score())

    for i, operation in enumerate(bot.pending_operations):
        bot.try_open_operation(i, candle)
    for i, operation in enumerate(bot.open_operations):
        bot.try_close_operation(i, candle)

    if (bot.status == "stalking"):
        started_regression = bot.started_regression(CCI)
        bot.last_cci = CCI
        if (started_regression):
            print("Empezó la regresion! Abrimos posicion")
            bot.create_position(candle['close'], candle['close-time'], CCI)
            bot.status = "waiting"
        return

    if (bot.reached_new_peak(CCI)):
        print("Señal disparada, esperando reversion! - Status actualizado a: stalking")
        bot.status = "stalking"
    bot.last_cci = CCI
