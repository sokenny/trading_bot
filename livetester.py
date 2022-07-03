import websocket, json
# from binance.client import Client
from binance import Client
import keys
import backtester

last_kline_start_time = None
last_klines = []

def livetest(config):

    client = Client(api_key=keys.Akey, api_secret=keys.Skey)

    PAIR = config["PAIR"].lower()
    INTERVAL = f'{config["KLINE_INTERVAL"]}m'
    socket = f'wss://fstream.binance.com/ws/{PAIR}@kline_{INTERVAL}'

    def kline_changed(this_kline_start_stime, last_kline_start_time):
        return this_kline_start_stime != last_kline_start_time and last_kline_start_time !=  None

    def on_message(ws, message):
        global last_kline_start_time
        global last_klines

        kline = json.loads(message)
        this_kline_start_stime = kline['k']['t']

        # Alguna clase de test para verificar que tengamos la longitud correcta de klines en el intervalo adecuado

        if(len(last_klines) == 0):
            INTERVALS = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE, 15: Client.KLINE_INTERVAL_15MINUTE}
            klines = client.get_historical_klines(config["PAIR"], INTERVALS[config["KLINE_INTERVAL"]], "2 hour ago UTC")
            print("Klines!", klines)
            last_klines = klines
            return klines

        if(kline_changed(this_kline_start_stime, last_kline_start_time)):
            print('Kline changed!')
            # Agregar esta Kline a last_klines y eliminar la mas vieja de todas

        print("last kline: ", last_kline_start_time, ' this kline: ', this_kline_start_stime)
        last_kline_start_time = this_kline_start_stime
        # CCI = calculateCCI(kline)
        # print(CCI)
        print(kline)

    def on_error(ws):
        print('Connection closed')

    ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error)

    print(ws.run_forever())

config = {"PAIR": "ROSEUSDT", "KLINE_INTERVAL": 1}
livetest(config)