from binance import Client
import keys
from Bot import Bot
from backtester import trade_over_candle
import os
import time

this_path = os.path.abspath(os.path.dirname(__file__))
kline_in_progress = {"start_time": None, "high": None, "low": None}
last_logged = None
livetester_started = int(time.time())
intervals = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE, 15: Client.KLINE_INTERVAL_15MINUTE}

def livetest(bot, trade_every, log_every):

    client = Client(api_key=keys.Akey, api_secret=keys.Skey)

    while(True):

        global last_logged
        global intervals

        if (last_logged == None or ((int(time.time()) - last_logged) >= log_every)):
            last_logged = int(time.time())
            log_report(bot)

        last_klines = client.get_historical_klines(bot.pair, intervals[bot.kline_interval], "2 hour ago UTC")

        dfc = bot.get_parsed_df_w_cci(last_klines)
        kline_to_analyse = dfc.iloc[-1]
        trade_over_candle(bot, kline_to_analyse)

        time.sleep(trade_every)

def log_report(bot):
    global livetester_started
    log_path = os.path.join(this_path, f'records/{livetester_started}.txt')
    to_log = f'\nTime: {int(time.time())}' \
             f'\nLast CCI: {bot.last_cci}' \
             f'\n# Pending operations: {len(bot.pending_operations)}' \
             f'\n# Open operations: {len(bot.open_operations)}' \
             f'\n# Closed operations: {str(bot.closed_positions)}\n\n'
    f = open(log_path, "a")
    f.write(str(to_log))
    f.close()

bot = Bot(mode="live", pair="ROSEUSDT", take_profit=3, stop_loss=25, position_structure=[{'weight': .5}, {'weight': .5}], cci_peak=50, operation_expiry_time=25000, start_gap_percentage=2, trade_amount=100, kline_interval=5, kline_to_use_in_prod=5, score_filter=0, score_longitude=10)
livetest(bot, trade_every=60, log_every=1800)