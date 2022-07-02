from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import backtester
import multibacktester
import keys
from Bot import Bot

HOST = keys.HOST
PORT = keys.PORT

def get_single_backtest(config):
    bot = Bot(mode="sandbox", pair=config['PAIR'], trade_amount=config['TRADE_AMOUNT'], take_profit=config['TAKE_PROFIT'], stop_loss=config['STOP_LOSS'], position_structure=eval(config['POSITION_STRUCTURE']), kline_to_use_in_prod=config['KLINE_TO_USE_IN_PROD'], kline_interval=config['KLINE_INTERVAL'], cci_peak=config['CCI_PEAK'], operation_expiry_time=config['OPERATION_EXPIRY_TIME'], score_filter=config['SCORE_FILTER'], score_longitude=config['SCORE_LONGITUDE'], start_gap_percentage=config['START_GAP_PERCENTAGE'])
    candles = bot.get_candle_sticks(eval(config['PERIOD']))
    backtest_log = backtester.backtest(bot, candles)
    return backtest_log

def get_multi_backtest(configs):
    parsed_configs = {}
    for key in configs.keys():
        parsed_configs[key] = eval(configs[key])
    backtest_log = multibacktester.backtest(parsed_configs)[0]
    return backtest_log

class NeuralHTTP(BaseHTTPRequestHandler):

    def get_parsed_data(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        raw_post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        print("raw data")
        print(raw_post_data)
        return json.loads(raw_post_data)

    def do_POST(self):
        data = self.get_parsed_data()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        print(data)
        if data["backtester"] == "single":
            print("pide single")
            backtest_log = get_single_backtest(data["config"])[0]
        elif data["backtester"] == "multi":
            print("pide multi")
            backtest_log = get_multi_backtest(data["configs"])
        self.wfile.write(bytes(backtest_log, "utf-8"))

def connect():
    server = HTTPServer((HOST, PORT), NeuralHTTP)
    server.serve_forever()
    server.server_close()
    print("Server now running")
    print(server)

connect()