import websocket, json
from binance import Client
import keys
from Bot import Bot
from backtester import trade_over_candle

kline_in_progress = {"start_time": None, "high": None, "low": None}
last_sealed_klines = []
last_event = None

def livetest(bot, trade_every):

    client = Client(api_key=keys.Akey, api_secret=keys.Skey)

    PAIR = bot.pair.lower()
    INTERVAL = f'{bot.kline_interval}m'
    socket = f'wss://fstream.binance.com/ws/{PAIR}@kline_{INTERVAL}'

    def on_message(ws, message):
        global kline_in_progress
        global last_sealed_klines
        global last_event

        kline = json.loads(message)
        this_kline_start_time = kline['k']['t']
        print(kline)

        if(last_event == None or ((kline['E'] - last_event) / 1000) >= trade_every):
            print(f'Podemos tradear! Transcurrieron  {trade_every} segundos.')
            last_event = kline['E']

        if(len(last_sealed_klines) == 0):
            INTERVALS = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE, 15: Client.KLINE_INTERVAL_15MINUTE}
            last_sealed_klines = client.get_historical_klines(bot.pair, INTERVALS[bot.kline_interval], "2 hour ago UTC")

        if (kline_in_progress["start_time"] == None):
            kline_in_progress["start_time"] = this_kline_start_time
            kline_in_progress["high"] = kline["k"]["h"]
            kline_in_progress["low"] = kline["k"]["l"]

        if (kline_changed(this_kline_start_time, kline_in_progress["start_time"])):
            print('Kline changed!')
            parsed_kline = parse_kline(kline, kline_in_progress)
            print("Parsed kline: ", parsed_kline)
            last_sealed_klines.append(parsed_kline)
            last_sealed_klines = last_sealed_klines[1:]
            kline_in_progress = {"start_time": this_kline_start_time, "high": kline['k']['h'], "low": kline['k']['l']}
            print('\nLEN DE LAST KLINES: ', len(last_sealed_klines))

        if(float(kline['k']['h'])>float(kline_in_progress['high'])):
            kline_in_progress['high'] = kline['k']['h']
        if (float(kline['k']['l']) < float(kline_in_progress['low'])):
            kline_in_progress['low'] = kline['k']['l']

        klines_to_analyse = last_sealed_klines.copy()
        klines_to_analyse.append(parse_kline(kline, kline_in_progress))
        dfc = bot.get_parsed_df_w_cci(klines_to_analyse)
        last_kline_to_analyse = dfc.iloc[-1]
        trade_over_candle(bot, last_kline_to_analyse)

    def kline_changed(this_kline_start_time, last_kline_start_time):
        return this_kline_start_time != last_kline_start_time and last_kline_start_time != None

    def parse_kline(kline, kline_in_progress):
        parsed_kline = []
        parsed_kline.append(kline['k']['t'])  # open time
        parsed_kline.append(kline['k']['o'])  # open price
        parsed_kline.append(kline_in_progress["high"])  # high
        parsed_kline.append(kline_in_progress["low"])  # low
        parsed_kline.append(kline['k']['c'])  # close price
        parsed_kline.append(None)  # volume (to calculate and can be dismissed)
        parsed_kline.append(kline['k']['T'])  # close time
        parsed_kline.append(None)  # quote asset volume (to calculate and can be dismissed)
        parsed_kline.append(None)  # number of trades (to calculate and can be dismissed)
        parsed_kline.append(None)  # taker buy base asset volume (to calculate and can be dismissed)
        parsed_kline.append(None)  # taker buy quote asset volume (to calculate and can be dismissed)
        parsed_kline.append(None)  # ignore (can be dismissed)
        return parsed_kline

    def on_error(ws):
        print('Connection closed')

    ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error)

    print(ws.run_forever())

bot = Bot(mode="live", pair="ROSEUSDT", take_profit=3, stop_loss=25, position_structure=[{'weight': .5}, {'weight': .5}], cci_peak=250, operation_expiry_time=2500, start_gap_percentage=2, trade_amount=100, kline_interval=5, kline_to_use_in_prod=5, score_filter=0, score_longitude=10)
livetest(bot, trade_every=60)