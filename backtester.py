import math
import sys
import io
from trade_over_candle import trade_over_candle

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