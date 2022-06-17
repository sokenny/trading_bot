import json
import keys
import pandas as pd
from binance.client import Client
import ta
import uuid
import time

client = Client(api_key=keys.Akey, api_secret=keys.Skey)

KLINE_STRUCTURE = ['open-time', 'open', 'high', 'low', 'close', 'volume', 'close-time', 'quote-asset-volume', 'number-of-trades', 'tbba-volume', 'tbqa-volume', 'ignore']
DEFAULT_CCI_LONGITUDE=20 # Cantidad de velas a ser tenidas en cuenta por el CCI por default

class Position:
    def __init__(self, status, start_price, end_price, stop_loss, amount, type, weight, create_time, trade_id):
        self.status = status
        self.start_price = round(start_price, 5)
        self.end_price = round(end_price, 5)
        self.stop_loss = round(stop_loss, 5)
        self.amount = amount
        self.type = type
        self.weight = weight
        self.create_time = create_time
        self.trade_id = trade_id

        self.open_time = None
        self.close_time = None
        self.outcome = None
        self.open_price = None
        self.exit_price = None

    def get(self):
        return {'status': self.status, 'start_price': self.start_price, 'end_price': self.end_price, 'stop_loss': self.stop_loss, 'amount': self.amount, 'type': self.type, 'open_price': self.open_price, 'exit_price': self.exit_price, 'weight': self.weight, 'open_time': self.open_time, 'close_time': self.close_time, 'outcome': self.outcome, 'trade_id': self.trade_id}

class Bot:
    def __init__(self, mode, pair, trade_amount, taker_profit, stop_loss, positions_structure, kline_to_use_in_prod, kline_interval, cci_peak):
        self.mode = mode
        self.pair = pair
        self.trade_amount = trade_amount
        self.taker_profit = taker_profit
        self.stop_loss = stop_loss
        self.positions_structure = positions_structure
        self.kline_to_use_in_prod = kline_to_use_in_prod
        self.kline_interval = kline_interval
        self.cci_peak = cci_peak
        self.default_cci_longitude = DEFAULT_CCI_LONGITUDE
        self.cci_longitude = int((self.kline_to_use_in_prod / self.kline_interval) * self.default_cci_longitude)

        self.status = "analysing"
        self.last_cci = None
        self.pending_positions = []
        self.open_positions = []
        self.closed_positions = []
        self.cci_signal = {'value':None, 'id':None}

    def get_candle_sticks(self, pair, KLINE_INTERVAL=5, PERIOD="15 days ago UTC"):
        INTERVALS = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE}
        candles = client.get_historical_klines(pair, INTERVALS[KLINE_INTERVAL], PERIOD)
        return candles

    def get_parsed_df(self, candles):
        dfc = pd.DataFrame(candles, columns=KLINE_STRUCTURE)
        dfc['high'] = dfc['high'].astype(float)
        dfc['low'] = dfc['low'].astype(float)
        dfc['close'] = dfc['close'].astype(float)
        return dfc

    def get_parsed_df_w_cci(self, candles):
        candlesDF = self.get_parsed_df(candles)
        CCI = ta.trend.CCIIndicator(candlesDF['high'], candlesDF['low'], candlesDF['close'], self.cci_longitude)
        candlesDFWCCI = candlesDF
        candlesDFWCCI['CCI'] = CCI.cci()
        return candlesDFWCCI

    def get_cci_df(self, high, low, close):
        CCI = ta.trend.CCIIndicator(high, low, close, self.cci_longitude)
        return CCI.cci()

    def get_cci(self, high, low, close):
        CCI = self.get_cci_df(high, low, close).tail(1).values[0]
        return CCI

    def reached_peak(self, CCI):
        return abs(CCI) > self.cci_peak

    def reached_new_peak(self, CCI):
        return self.reached_peak(CCI) and not self.reached_peak(self.last_cci)

    def get_position_type(self, CCI):
        return "short" if CCI > 0 else "long"

    def started_regression(self, CCI):
        return CCI > self.last_cci if self.last_cci < 0 else CCI < self.last_cci

    def get_price_variation(self, this_price, price_when_trade_opened):
        return (price_when_trade_opened - this_price) / price_when_trade_opened * 100

    def has_won(self, last_cci, price_variation):
        return price_variation > 0 if last_cci < 0 else price_variation < 0

    def get_operator(self, CCI):
        return -1 if self.get_position_type(CCI) == "long" else 1

    def get_positions_to_create(self, price, create_time, CCI):
        price_position_multiplier = (self.taker_profit / len(self.positions_structure)) / 100
        positions_to_create = []
        operator = self.get_operator(CCI)
        position_type = self.get_position_type(CCI)
        print("CCI: ", CCI, " - opp: ", operator, ' - pos type: ', position_type)
        for i, p in enumerate(self.positions_structure):
            amount = self.trade_amount * p['weight']
            start_price = price + (((price * price_position_multiplier) * (i + 1))) * operator
            end_price = start_price + ((start_price * (self.taker_profit / 100))) * -operator
            stop_loss = start_price + ((start_price * (self.stop_loss / 100))) * operator
            positions_to_create.append(Position("pending", start_price, end_price, stop_loss, amount, position_type, p['weight'], create_time,  str(uuid.uuid4())))
        return positions_to_create

    def create_positions(self, price, candle_time, CCI):
        actual_time = int(time.time() * 1000)
        create_time = candle_time if self.mode == "sandbox" else actual_time
        positions_to_create = self.get_positions_to_create(price, create_time, CCI)
        for position in positions_to_create:
            self.pending_positions.append(position)
            print('pos pending: ', position.get())

    def try_open_position(self, pending_position_index, candle):
        position = self.pending_positions[pending_position_index]
        can_open_position = candle['close'] <= position.start_price if position.type == "long" else candle['close'] >= position.start_price
        if(can_open_position):
            position.open_time = candle['close-time']
            position.status = "open"
            position.open_price = candle['close']
            self.open_position(pending_position_index)
            return True
        return False

    def open_position(self, pending_position_index):
        print('Opened position: ', self.pending_positions[pending_position_index].get())
        self.open_positions.append(self.pending_positions[pending_position_index])
        del self.pending_positions[pending_position_index]

    def try_close_position(self, open_position_index, candle):
        position = self.open_positions[open_position_index]
        lost_position = candle['close'] <= position.stop_loss if position.type == "long" else candle['close'] >= position.stop_loss
        won_position = candle['close'] >= position.end_price if position.type == "long" else candle['close'] <= position.end_price
        if(won_position or lost_position):
            position.close_time = candle['close-time']
            position.outcome = 1 if won_position else 0
            position.exit_price = candle['close']
            position.status = "closed"
            self.close_position(open_position_index)
            return True
        return False

    def close_position(self, position_index):
        print('Closed position: ', self.open_positions[position_index].get())
        self.closed_positions.append(self.open_positions[position_index].get())
        del self.open_positions[position_index]


def txt_to_json(path):
    txt = open(path, "r")
    txt = txt.read()
    txt = txt.replace("\'", "\"")
    json_output = json.loads(txt)
    return json_output



