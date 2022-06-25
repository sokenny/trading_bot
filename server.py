from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import backtester
import keys
from Bot import Bot

HOST = keys.HOST
PORT = keys.PORT

class NeuralHTTP(BaseHTTPRequestHandler):

    def get_parsed_data(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        raw_post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        return json.loads(raw_post_data)

    def do_POST(self):
        data = self.get_parsed_data()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        bot = Bot(mode="sandbox", pair=data['PAIR'], trade_amount=data['TRADE_AMOUNT'], taker_profit=data['TAKER_PROFIT'], stop_loss=data['STOP_LOSS'], positions_structure=eval(data['POSITIONS_STRUCTURE']),  kline_to_use_in_prod=data['KLINE_TO_USE_IN_PROD'], kline_interval=data['KLINE_INTERVAL'], cci_peak=data['CCI_PEAK'], position_expiry_time=data['POSITION_EXPIRY_TIME'], score_filter=data['SCORE_FILTER'], score_longitude=data['SCORE_LONGITUDE'], start_gap_percentage=data['START_GAP_PERCENTAGE'])
        self.wfile.write(bytes(backtester.backtest(bot, period=eval(data['PERIOD'])), "utf-8"))

def connect():
    server = HTTPServer((HOST, PORT), NeuralHTTP)
    server.serve_forever()
    server.server_close()
    print("Server now running")
    print(server)

connect()