from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import keys
import controller

HOST = keys.HOST
PORT = keys.PORT

class NeuralHTTP(BaseHTTPRequestHandler):

    def get_parsed_data(self):
        content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        raw_post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        return json.loads(raw_post_data)

    def do_POST(self):
        data = self.get_parsed_data()
        print(data)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if data["backtester"] == "single":
            print("pide single")
            backtest_log = controller.get_single_backtest(data["config"])[0]
        elif data["backtester"] == "multi":
            print("pide multi")
            backtest_log = controller.get_multi_backtest(data["configs"])
        self.wfile.write(bytes(backtest_log, "utf-8"))

def connect():
    server = HTTPServer((HOST, PORT), NeuralHTTP)
    server.serve_forever()
    server.server_close()
    print("Server now running")
    print(server)

connect()