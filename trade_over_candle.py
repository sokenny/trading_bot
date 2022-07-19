def trade_over_candle(bot, candle):

    CCI = candle['CCI']
    print_tick_report(bot, candle)

    for i, operation in enumerate(bot.pending_operations):
        bot.try_open_operation(i, candle)
    for i, operation in enumerate(bot.open_operations):
        bot.try_close_operation(i, candle)

    if (bot.status == "stalking"):
        started_regression = bot.started_regression(CCI)
        bot.last_cci = CCI
        if (started_regression):
            print("Empezó la regresion! Intentamos abrir posición.")
            bot.try_create_position(candle['close'], candle['close-time'], CCI)
            bot.status = "waiting"
        return

    if (bot.reached_new_peak(CCI)):
        print("Señal disparada, esperando regresión! - Status actualizado a: stalking.")
        bot.status = "stalking"
    bot.last_cci = CCI

def print_tick_report(bot, candle):
    print(f'\nCCI: , {candle["CCI"]} - time:  {candle["close-time"]} - bot status: ', bot.status, ' - candle price: ',
          candle['close'], ' - score: ', bot.get_score(), ' - weights in use: ', bot.get_allocated_weights())