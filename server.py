from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import main
import keys

HOST = keys.HOST
PORT = keys.PORT

class NeuralHTTP(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        raw_post_data = self.rfile.read(content_length) # <--- Gets the data itself
        data = json.loads(raw_post_data)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(main.backtest(__PAIR=data['PAIR'], __PERIOD=eval(data['PERIOD']),  __TRADE_AMOUNT=data['TRADE_AMOUNT'], __TAKER_PROFIT=data['TAKER_PROFIT'], __STOP_LOSS=data['STOP_LOSS'], __POSITIONS_STRUCTURE=eval(data['POSITIONS_STRUCTURE']),  __KLINE_TO_USE_IN_PROD=data['KLINE_TO_USE_IN_PROD'], __KLINE_INTERVAL=data['KLINE_INTERVAL'], __CCI_PEAK=data['CCI_PEAK'], __POSITION_EXPIRY_TIME=data['POSITION_EXPIRY_TIME'], __SCORE_FILTER=data['SCORE_FILTER'], __SCORE_LONGITUDE=data['SCORE_LONGITUDE'], __START_GAP_PERCENTAGE=data['START_GAP_PERCENTAGE']), "utf-8"))

def connect():
    server = HTTPServer((HOST, PORT), NeuralHTTP)
    server.serve_forever()
    server.server_close()
    print("Server now running")
    print(server)

connect()