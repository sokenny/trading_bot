import copy
import uuid
import keys
import pandas as pd
from binance.client import Client
import ta
import time
import config
from Operation import Operation


binance_client = Client(api_key=keys.Akey, api_secret=keys.Skey)
KLINE_STRUCTURE = ['open-time', 'open', 'high', 'low', 'close', 'volume', 'close-time', 'quote-asset-volume', 'number-of-trades', 'tbba-volume', 'tbqa-volume', 'ignore']

class Bot:
    def __init__(self, mode, pair, trade_amount, take_profit, stop_loss, position_structure, kline_to_use_in_prod, kline_interval, cci_peak, operation_expiry_time, start_gap_percentage, max_weight_allocation, id=False):
        self.id = id or str(uuid.uuid4())
        self.mode = mode
        self.pair = pair
        self.trade_amount = trade_amount
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.position_structure = position_structure
        self.kline_to_use_in_prod = kline_to_use_in_prod
        self.kline_interval = kline_interval
        self.cci_peak = cci_peak
        self.default_cci_longitude = config.DEFAULT_CCI_LONGITUDE
        self.cci_longitude = int((self.kline_to_use_in_prod / self.kline_interval) * self.default_cci_longitude)
        self.operation_expiry_time = operation_expiry_time
        self.start_gap_percentage = start_gap_percentage
        self.max_weight_allocation = max_weight_allocation

        self.status = "analysing"
        self.last_cci = None
        self.pending_operations = []
        self.open_operations = []
        self.closed_operations = []
        self.last_candle = None
        self.step_size = self.__get_step_size() if self.mode == "live-trade" else False

    def __get_step_size(self):
        print("Fetching step size")
        exchange_info = binance_client.futures_exchange_info()
        for symbol_info in exchange_info['symbols']:
            if (symbol_info['symbol'] == self.pair):
                step_size = symbol_info['filters'][1]['stepSize']
                print("Step size: ", step_size)
                return float(step_size)
        return False

    def get_candle_sticks(self, PERIOD):
        INTERVALS = {1: Client.KLINE_INTERVAL_1MINUTE, 5: Client.KLINE_INTERVAL_5MINUTE, 15: Client.KLINE_INTERVAL_15MINUTE}
        candles = binance_client.get_historical_klines(self.pair, INTERVALS[self.kline_interval], *PERIOD)
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

    def get_allocated_weights(self):
        weights = 0
        for operation in self.pending_operations:
            weights += operation.weight
        for operation in self.open_operations:
            weights += operation.weight
        return weights

    def get_position_weight(self):
        weights = 0
        for operation in self.position_structure:
            weights += operation["weight"]
        return weights

    def reached_peak(self, CCI):
        if(CCI == None):
            return False
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

    def get_position_to_create(self, price, create_time, CCI):
        price_position_multiplier = (self.take_profit / len(self.position_structure)) / 100
        position_to_create = []
        operator = self.get_operator(CCI)
        position_type = self.get_position_type(CCI)
        position_id = str(uuid.uuid4())
        for i, operation in enumerate(self.position_structure):
            amount = self.trade_amount * operation['weight']
            start_price = price + (((price * price_position_multiplier) * (i + 1)) + ((self.start_gap_percentage / 100) * price)) * operator
            end_price = start_price + ((start_price * (self.take_profit / 100))) * -operator
            stop_loss = start_price + ((start_price * (self.stop_loss / 100))) * operator
            position_to_create.append(Operation("pending", start_price, end_price, stop_loss, amount, position_type, operation['weight'], create_time,  position_id))
        return position_to_create

    def try_create_position(self, price, candle_time, CCI):
        if(self.get_allocated_weights() + self.get_position_weight() > self.max_weight_allocation):
            print("No pudimos abrir posicion")
            return False
        else:
            actual_time = int(time.time() * 1000)
            create_time = candle_time if self.mode == "sandbox" else actual_time
            position_to_create = self.get_position_to_create(price, create_time, CCI)
            print("Opened position!")
            for operation in position_to_create:
                if (self.mode == "live-trade"):
                    self.__create_operation(operation)
                else:
                    self.pending_operations.append(operation)
                    print('Created operation: ', operation.get())

    def __create_operation(self, operation):
        order_to_create = self.__get_order_to_create(operation)
        print("Order to create: ", order_to_create)
        if(binance_client.futures_create_order(timestamp=time.time(), **order_to_create)):
            self.pending_operations.append(operation)
            print("__create_operation: Binance order created!")

    def __get_order_to_create(self, operation):
        trimmed_quantity = self.__get_trimmed_quantity(operation.quantity)
        side = "BUY" if operation.type == "long" else "SELL"
        order = {"symbol": self.pair, "side": side, "positionSide": operation.type.upper(), "timeInForce": "GTC", "type": "LIMIT", "quantity": trimmed_quantity, "price": operation.start_price, "newClientOrderId": operation.id }
        return order

    def __get_trimmed_quantity(self, quantity):
        trimmed_quantity = quantity - (quantity % self.step_size)
        return trimmed_quantity

    def try_open_operation(self, pending_operation_index, candle):
        operation = self.pending_operations[pending_operation_index]
        operation_expired = self.try_expire_operation(pending_operation_index, candle)
        if(not operation_expired):
            if(self.mode == "live-trade"):
                self.__if_filled_open_operation(operation, pending_operation_index)
            else:
                can_open_operation = candle['close'] <= operation.start_price if operation.type == "long" else candle['close'] >= operation.start_price
                if(can_open_operation):
                    operation.open_time = candle['close-time']
                    operation.status = "open"
                    operation.open_price = candle['close']
                    self.open_operation(pending_operation_index)
                    return True
            return False
        return False

    def __if_filled_open_operation(self, operation, pending_operation_index):
        order = binance_client.futures_get_order(timestamp=time.time(), origClientOrderId=operation.id, symbol=self.pair)
        if(order["status"] == "FILLED"):
            operation.open_time = round(time.time())
            operation.status = "open"
            operation.open_price = order["price"]
            self.open_operation(pending_operation_index)

    def try_expire_operation(self, pending_operation_index, candle):
        operation = self.pending_operations[pending_operation_index]
        pending_lifetime = (candle['close-time'] - operation.create_time) / 1000
        if(pending_lifetime > self.operation_expiry_time):
            print('La siguiente posición expiró: ', self.pending_operations[pending_operation_index].get())
            if(self.mode == "live-trade"):
                if(not self.__expire_operation(operation)):
                    print("Failed to expire operation: ", operation)
                    return False
            del self.pending_operations[pending_operation_index]
            return True
        return False

    def __expire_operation(self, operation):
        print("Operation to expire: ", operation.id)
        closed_order = binance_client.futures_cancel_order(timestamp=time.time(), symbol=self.pair, origClientOrderId=operation.id)
        return closed_order["status"] == "CANCELED"

    def __close_tpsls(self, operation):
        errors = 0
        for tpsl_order_id in [self.__get_tpsl_id(operation, 'tp'), self.__get_tpsl_id(operation, 'sl')]:
            try:
                closed_tpsl = binance_client.futures_cancel_order(timestamp=time.time(), symbol=self.pair, origClientOrderId=tpsl_order_id)
                if (closed_tpsl):
                    print("Successfully closed tpsl: ", closed_tpsl)
            except Exception as e:
                errors +=1
                print("Failed to close tpsl: ", e)
        return errors == 0

    def __get_tpsl_id(self, operation, tpsl_type):
        return f'{operation.id[:30]}-{tpsl_type}'

    def open_operation(self, pending_operation_index):
        print('Opened operation: ', self.pending_operations[pending_operation_index].get())
        self.open_operations.append(self.pending_operations[pending_operation_index])
        del self.pending_operations[pending_operation_index]
        if(self.mode == "live-trade"):
            self.__create_tp_sl(self.open_operations[-1])

    def __create_tp_sl(self, operation):
        side = "SELL" if operation.type == "long" else "BUY"
        take_profit_order = {"side": side, "price": operation.end_price, "positionSide": operation.type.upper(), "timeInForce": "GTC", "type": "TAKE_PROFIT", "quantity": self.__get_trimmed_quantity(operation.quantity), "stopPrice": operation.end_price, "newClientOrderId": self.__get_tpsl_id(operation, 'tp') }
        stop_loss_order = {"side": side, "price": operation.stop_loss, "positionSide": operation.type.upper(), "timeInForce": "GTC", "type": "STOP", "quantity": self.__get_trimmed_quantity(operation.quantity), "stopPrice": operation.stop_loss, "newClientOrderId": self.__get_tpsl_id(operation, 'sl') }
        tpsls_created = 0
        for i, order in enumerate([take_profit_order, stop_loss_order]):
            print("tpsl to create: ", order)
            created_tpsl_order = binance_client.futures_create_order(timestamp=time.time(), symbol=self.pair, **order)
            if(created_tpsl_order):
                print("Created tpsl order: ", created_tpsl_order)
                tpsls_created += 1
        return tpsls_created == 2

    def try_close_operation(self, open_operation_index, candle):
        operation = self.open_operations[open_operation_index]
        if(self.mode == "live-trade"):
            return self.__if_any_tpsl_filled_close_operation(operation, open_operation_index)
        else:
            lost_position = candle['close'] <= operation.stop_loss if operation.type == "long" else candle['close'] >= operation.stop_loss
            won_position = candle['close'] >= operation.end_price if operation.type == "long" else candle['close'] <= operation.end_price
            closed = won_position or lost_position
            if(closed):
                operation.close_time = candle['close-time']
                operation.outcome = 1 if won_position else 0
                operation.exit_price = candle['close']
                operation.status = "closed"
                self.close_operation(open_operation_index)
            return closed

    def __if_any_tpsl_filled_close_operation(self, operation, open_operation_index):
        closed = False
        for tpsl_order_id in [self.__get_tpsl_id(operation, 'tp'), self.__get_tpsl_id(operation, 'sl')]:
            order = binance_client.futures_get_order(timestamp=time.time(), origClientOrderId=tpsl_order_id,
                                                     symbol=self.pair)
            if (order["status"] == "FILLED"):
                print("TPSL filled, we try close the opposing tpsl")
                closed = True
                self.__close_tpsls(operation)
        if (closed):
            self.close_operation(open_operation_index)
        return closed

    def close_operation(self, operation_index):
        print('Closed operation: ', self.open_operations[operation_index].get())
        self.closed_operations.append(self.open_operations[operation_index].get())
        del self.open_operations[operation_index]

    def get_score(self, last_positions="all"):
        score = 0
        if(isinstance(last_positions, list)):
            positions_to_iterate = self.closed_operations[last_positions[0]:last_positions[1]]
        else:
            positions_to_iterate  = self.closed_operations[0 if last_positions == "all" else -last_positions:]
        for position in positions_to_iterate:
            if(position['outcome'] == 0):
                score -= position['weight'] * self.stop_loss
            else:
                score += position['weight'] * self.take_profit
        return score

    def get_segments_score(self):
        c_p_length = len(self.closed_operations)
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
        del instantiation['pending_operations']
        del instantiation['closed_operations']
        del instantiation['open_operations']
        del instantiation['last_candle']
        return instantiation

    def get_footer_report(self, print_report=False):
        footer_report = {"won": 0, "won_weights": 0, "lost": 0, "lost_weights": 0, "positions_left_open": len(self.open_operations), "score": self.get_score(), "config": self.get_config()}
        for position in self.closed_operations:
            if (position['outcome'] == 1):
                footer_report["won"] += 1
                footer_report["won_weights"] += position['weight']
            else:
                footer_report["lost"] += 1
                footer_report["lost_weights"] += position['weight']
        footer_report["won_weights"] = round(footer_report["won_weights"], 3)
        footer_report["lost_weights"] = round(footer_report["lost_weights"], 3)
        footer_report["lost_weights"] = round(footer_report["lost_weights"], 3)
        footer_report["score"] = round(footer_report["score"], 3)
        if(print_report):
            print("\n\nOperations left open: ", footer_report["positions_left_open"])
            for position in self.open_operations:
                parsed_position = position.get()
                parsed_position["_last_price"] = self.last_candle["close"]
                parsed_position["_price_variation"] = -self.get_price_variation(self.last_candle["close"], parsed_position["open_price"])
                print(parsed_position)
            print('\nWon: ', footer_report["won"], ' - Won weights: ', footer_report["won_weights"])
            print('Lost: ', footer_report["lost"], ' - Lost weights: ', footer_report["lost_weights"])
            print('Score: ', footer_report["score"])
            print("Segments score: ", self.get_segments_score(), "\n")
            print("CONFIG USED: ")
            print(self.get_config())
        return footer_report