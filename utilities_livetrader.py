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

def get_order():
    orderId = 1804865616
    params = {"timestamp": time.time(), "orderId": orderId, "symbol": SYMBOL}
    response = client.futures_get_order(**params)
    print("Get order response: ", response)

def create_order(order):
    response = client.futures_create_order(**order)
    print("Create order res: ", response)

def create_multiple_orders(orders):
    params = {"timestamp": time.time(), "batchOrders": orders}
    response = client.futures_place_batch_order(**params)
    print("Response de create multiple orders: ", response)

set_hedgemode()
set_margin_type()
set_leverage()
get_order()

orders_to_open = [
    {"symbol": SYMBOL, "side": "BUY", "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "LIMIT", "quantity": QUANTITY, "price": PRICE, "newClientOrderId": str(uuid.uuid4()) },
    {"symbol": SYMBOL, "side": "BUY", "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "LIMIT", "quantity": QUANTITY, "price": PRICE_2, "newClientOrderId": str(uuid.uuid4()) },
    # {"symbol": SYMBOL, "side": "SELL", "price": TAKE_PROFIT, "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "TAKE_PROFIT", "quantity": QUANTITY, "stopPrice": TAKE_PROFIT, "newClientOrderId": str(uuid.uuid4()) },
    # {"symbol": SYMBOL, "side": "SELL", "price": STOP_LOSS, "positionSide": POSITION_SIDE, "timeInForce": "GTC", "type": "STOP", "quantity": QUANTITY, "stopPrice": STOP_LOSS, "newClientOrderId": str(uuid.uuid4()) }
]

# create_order(orders_to_open[1])
# create_order(orders_to_open[2])
# create_multiple_orders(orders_to_open)