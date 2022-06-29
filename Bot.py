import copy
import keys
import pandas as pd
from binance.client import Client
import ta
import time
import config
from Position import Position

client = Client(api_key=keys.Akey, api_secret=keys.Skey)
KLINE_STRUCTURE = ['open-time', 'open', 'high', 'low', 'close', 'volume', 'close-time', 'quote-asset-volume', 'number-of-trades', 'tbba-volume', 'tbqa-volume', 'ignore']

class Bot:
    def __init__(self, mode, pair, trade_amount, taker_profit, stop_loss, positions_structure, kline_to_use_in_prod, kline_interval, cci_peak, position_expiry_time, score_filter, score_longitude, start_gap_percentage):
        self.mode = mode
        self.pair = pair
        self.trade_amount = trade_amount
        self.taker_profit = taker_profit
        self.stop_loss = stop_loss
        self.positions_structure = positions_structure
        self.kline_to_use_in_prod = kline_to_use_in_prod
        self.kline_interval = kline_interval
        self.cci_peak = cci_peak
        self.default_cci_longitude = config.DEFAULT_CCI_LONGITUDE
        self.cci_longitude = int((self.kline_to_use_in_prod / self.kline_interval) * self.default_cci_longitude)
        self.position_expiry_time = position_expiry_time
        self.score_filter = score_filter
        self.score_longitude = score_longitude
        self.start_gap_percentage = start_gap_percentage

        self.status = "analysing"
        self.last_cci = None
        self.pending_positions = []
        self.open_positions = []
        self.closed_positions = []

    def get_candle_sticks(self, PERIOD):
        INTERVALS = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE, 15: Client.KLINE_INTERVAL_15MINUTE}
        candles = client.get_historical_klines(self.pair, INTERVALS[self.kline_interval], *PERIOD)
        return candles

    def get_parsed_df(self, candles):
        dfc = pd.DataFrame(candles, columns=KLINE_STRUCTURE)
        dfc['high'] = dfc['high'].astype(float)
        dfc['low'] = dfc['low'].astype(float)
        dfc['close'] = dfc['close'].astype(float)
        return dfc

    def get_parsed_df_w_cci(self, candles):
        candlesDF = self.get_parsed_df(candles)
        CCI_df = ta.trend.CCIIndicator(candlesDF['high'], candlesDF['low'], candlesDF['close'], self.cci_longitude)
        candlesDFWCCI = candlesDF
        candlesDFWCCI['CCI'] = CCI_df.cci()
        return candlesDFWCCI

    def get_cci_df(self, high, low, close):
        CCI = ta.trend.CCIIndicator(high, low, close, self.cci_longitude)
        return CCI.cci()

    def get_cci(self, high, low, close):
        CCI = self.get_cci_df(high, low, close).tail(1).values[0]
        return CCI

    def reached_peak(self, CCI):
        if(CCI == None):
            return False
        return abs(CCI) > self.cci_peak

    def reached_new_peak(self, CCI):
        return self.reached_peak(CCI) and not self.reached_peak(self.last_cci)

    def get_position_type(self, CCI):
        return "short" if CCI > 0 else "long"

    def get_layer(self):
        return 2 if self.get_score(last_positions=self.score_longitude) > self.score_filter else 1

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
        layer = self.get_layer()
        for i, p in enumerate(self.positions_structure):
            amount = self.trade_amount * p['weight']
            start_price = price + (((price * price_position_multiplier) * (i + 1)) + ((self.start_gap_percentage / 100) * price)) * operator
            end_price = start_price + ((start_price * (self.taker_profit / 100))) * -operator
            stop_loss = start_price + ((start_price * (self.stop_loss / 100))) * operator
            positions_to_create.append(Position("pending", start_price, end_price, stop_loss, amount, position_type, p['weight'], create_time,  layer))
        return positions_to_create

    def create_positions(self, price, candle_time, CCI):
        actual_time = int(time.time() * 1000)
        create_time = candle_time if self.mode == "sandbox" else actual_time
        positions_to_create = self.get_positions_to_create(price, create_time, CCI)
        for position in positions_to_create:
            print('Created position: ', position.get())
            self.pending_positions.append(position)

    def try_open_position(self, pending_position_index, candle):
        position = self.pending_positions[pending_position_index]
        position_expired = self.try_expire_position(pending_position_index, candle)
        if(not position_expired):
            can_open_position = candle['close'] <= position.start_price if position.type == "long" else candle['close'] >= position.start_price
            if(can_open_position):
                position.open_time = candle['close-time']
                position.status = "open"
                position.open_price = candle['close']
                self.open_position(pending_position_index)
                return True
            return False
        return False

    def try_expire_position(self, pending_position_index, candle):
        position = self.pending_positions[pending_position_index]
        pending_lifetime = (candle['close-time'] - position.create_time) / 1000
        if(pending_lifetime > self.position_expiry_time):
            print('La siguiente posición expiró: ', self.pending_positions[pending_position_index].get())
            del self.pending_positions[pending_position_index]
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

    def get_score(self, last_positions="all", target_layer=False):
        score = 0
        if(isinstance(last_positions, list)):
            positions_to_iterate = self.closed_positions[last_positions[0]:last_positions[1]]
        else:
            positions_to_iterate  = self.closed_positions[0 if last_positions == "all" else -last_positions:]
        for position in positions_to_iterate:
            if target_layer and position['layer'] != target_layer:
                continue
            if(position['outcome'] == 0):
                score -= position['weight'] * self.stop_loss
            else:
                score += position['weight'] * self.taker_profit
        return score

    def get_segments_score(self):
        c_p_length = len(self.closed_positions)
        positions_per_segment = c_p_length / 6
        segments_score = {"won": 0, "lost": 0}
        for i in range(6):
            from_i = round(i * positions_per_segment)
            to_i = round((i + 1) * positions_per_segment)
            score = self.get_score(last_positions=[from_i, to_i])
            segments_score["won" if score > 0 else "lost"] += 1
        return segments_score

    def get_config(self):
        instantiation = copy.deepcopy(vars(self))
        del instantiation['pending_positions']
        del instantiation['closed_positions']
        del instantiation['open_positions']
        return instantiation

    def get_footer_report(self, print_report=False):
        footer_report = {"won": 0, "won_weights": 0, "lost": 0, "lost_weights": 0, "positions_left_open": len(self.open_positions), "layer_1_score": self.get_score(), "layer_2_score": self.get_score(target_layer=2), "config": self.get_config()}
        for position in self.closed_positions:
            if (position['outcome'] == 1):
                footer_report["won"] += 1
                footer_report["won_weights"] += position['weight']
            else:
                footer_report["lost"] += 1
                footer_report["lost_weights"] += position['weight']
        footer_report["won_weights"] = round(footer_report["won_weights"], 3)
        footer_report["lost_weights"] = round(footer_report["lost_weights"], 3)
        footer_report["lost_weights"] = round(footer_report["lost_weights"], 3)
        footer_report["layer_1_score"] = round(footer_report["layer_1_score"], 3)
        footer_report["layer_2_score"] = round(footer_report["layer_2_score"], 3)
        if(print_report):
            print("\n\nPositions left open: ", footer_report["positions_left_open"])
            for position in self.open_positions:
                print(position.get())
            print('\nWon: ', footer_report["won"], ' - Won weights: ', footer_report["won_weights"])
            print('Lost: ', footer_report["lost"], ' - Lost weights: ', footer_report["lost_weights"])
            print('Layer 1 score: ', footer_report["layer_1_score"])
            print("Layer 2 score: ", footer_report["layer_2_score"])
            print("Segments score (layer1): ", self.get_segments_score(), "\n")
            print("CONFIG USED: ")
            print(self.get_config())
        return footer_report