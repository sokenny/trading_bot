import uuid
import keys
from binance.client import Client
import time

client = Client(api_key=keys.Akey, api_secret=keys.Skey)

SYMBOL = "ROSEUSDT"
POSITION_SIDE = "LONG"
QUANTITY = 100
PRICE = 0.05190
PRICE_2 = 0.05195
ORDER_ID = str(uuid.uuid4())
LEVERAGE = 1
TAKE_PROFIT = round(PRICE * 1.01, 5)
STOP_LOSS = round(PRICE - (PRICE*0.25), 5)

def set_hedgemode():
    params = {"timestamp": time.time(), "dualSidePosition": "true"}
    try:
        client.futures_change_position_mode(**params)
    except:
        print("You are probably already set to hedge mode")
    positions_mode = client.futures_get_position_mode(timestamp=time.time())
    print("Hedge mode set!") if(positions_mode['dualSidePosition']) else print("Could not set hedge mode")

def set_margin_type():
    params = {"symbol":SYMBOL, "marginType": "ISOLATED", "timestamp": time.time()}
    try:
        response = client.futures_change_margin_type(**params)
        print("Response: ", response)
    except:
        print("Margin type is probably already set to isolate")

def set_leverage():
    params = {"symbol":SYMBOL, "leverage": LEVERAGE, "timestamp": time.time()}
    response = client.futures_change_leverage(**params)
    print("Leverage response: ", response)

def initialize_trading_configuration():
    set_hedgemode()
    set_margin_type()
    set_leverage()

def get_order():
    # orderId = 1828399913
    clientOrderId = '822de9a5-350a-440c-afac-a0a514-sl'
    params = {"timestamp": time.time(), "origClientOrderId": clientOrderId, "symbol": SYMBOL}
    response = client.futures_get_order(**params)
    print("Get order response: ", response)

def create_order(order):
    response = client.futures_create_order(**order)
    print("Create order res: ", response)

def create_multiple_orders(orders):
    params = {"timestamp": time.time(), "batchOrders": orders}
    response = client.futures_place_batch_order(**params)
    print("Response de create multiple orders: ", response)

def get_step_size(symbol):
    exchange_info = client.futures_exchange_info()
    for symbol_info in exchange_info['symbols']:
        if(symbol_info['symbol'] == symbol):
            step_size = symbol_info['filters'][1]['stepSize']
            print("Step size: ", step_size)
            print(symbol_info)

# initialize_trading_configuration()
get_order()
get_step_size("ROSEUSDT")
# print(client.futures_cancel_order(timestamp=time.time(), symbol="ROSEUSDT", origClientOrderId='1549fb9a-dcb8-4489-93da-af161000212e'))
orders_to_open = [
    {"symbol": SYMBOL, "side": "BUY", "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "LIMIT", "quantity": QUANTITY, "price": PRICE, "newClientOrderId": str(uuid.uuid4()) },
    {"symbol": SYMBOL, "side": "BUY", "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "LIMIT", "quantity": QUANTITY, "price": PRICE_2, "newClientOrderId": str(uuid.uuid4()) },
    # {"symbol": SYMBOL, "side": "SELL", "price": TAKE_PROFIT, "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "TAKE_PROFIT", "quantity": QUANTITY, "stopPrice": TAKE_PROFIT, "newClientOrderId": str(uuid.uuid4()) },
    # {"symbol": SYMBOL, "side": "SELL", "price": STOP_LOSS, "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "STOP", "quantity": QUANTITY, "stopPrice": STOP_LOSS, "newClientOrderId": str(uuid.uuid4()) }
]

# create_order(orders_to_open[1])
# create_order(orders_to_open[2])
# create_multiple_orders(orders_to_open)