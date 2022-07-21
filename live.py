from binance import Client
import keys
from trade_over_candle import trade_over_candle
import os
import time
from classes.Operation import Operation
import copy

this_path = os.path.abspath(os.path.dirname(__file__))
last_logged = None
bot_started = int(time.time())

def operate(initial_bot, trade_every, log_every):

    bot_path = os.path.join(this_path, f'traders/records/{initial_bot.id}')
    create_bot_directory(initial_bot, bot_path)

    bot = get_bot_state(initial_bot, bot_path)
    client = Client(api_key=keys.Akey, api_secret=keys.Skey)
    register_config(bot, bot_path)

    while(True):

        global last_logged
        global intervals

        if (last_logged == None or ((int(time.time()) - last_logged) >= log_every)):
            last_logged = int(time.time())
            log_report(bot, bot_path)

        last_klines = client.get_historical_klines(bot.pair, Client.KLINE_INTERVAL_5MINUTE, "2 hour ago UTC")

        dfc = bot.get_parsed_df_w_cci(last_klines)
        kline_to_analyse = dfc.iloc[-1]
        trade_over_candle(bot, kline_to_analyse)

        store_bot_state(bot, bot_path)

        time.sleep(trade_every)

def get_bot_state(bot, bot_path):
    bot_copy = copy.deepcopy(bot)
    state = get_json_file_contents(f'{bot_path}/state.txt')
    bot_copy.status = state['status']
    bot_copy.last_cci = state['last_cci']
    bot_copy.pending_operations = get_instantiated_operations(state["pending_operations"])
    bot_copy.open_operations = get_instantiated_operations(state["open_operations"])
    bot_copy.closed_operations = state["closed_operations"]
    return bot_copy

def get_instantiated_operations(operations):
    instantiated_operations = []
    for operation in operations:
        instantiated_operation = Operation(operation["status"], operation["start_price"], operation["end_price"], operation["stop_loss"], operation["amount"], operation["type"], operation["weight"], operation["create_time"], operation["position_id"], id=operation["id"])
        instantiated_operations.append(instantiated_operation)
    return instantiated_operations

def store_bot_state(bot, bot_path):
    bot_state = {"status": bot.status, "last_cci": bot.last_cci, "closed_operations": bot.closed_operations}
    bot_state["pending_operations"] = parse_operations(bot.pending_operations)
    bot_state["open_operations"] = parse_operations(bot.open_operations)
    f = open(f'{bot_path}/state.txt', "w")
    f.write(str(bot_state))
    f.close()

def parse_operations(operations):
    parsed_operations = []
    for operation in operations:
        parsed_operations.append(operation.get())
    return parsed_operations

def get_json_file_contents(file_path):
    exists = os.path.exists(file_path)
    if(exists):
        file_contents = open(file_path, "r")
        file_contents = file_contents.read()
        file_contents = eval(file_contents)
        return file_contents
    return False

def create_bot_directory(bot, bot_path):
    dir_exists = os.path.exists(bot_path)
    if not dir_exists:
        os.makedirs(bot_path)
        initial_bot_state = {"status": bot.status, "last_cci": bot.last_cci, "pending_operations": bot.pending_operations, "open_operations": bot.open_operations, "closed_operations": bot.closed_operations}
        f = open(f'{bot_path}/state.txt', "w")
        f.write(str(initial_bot_state))
        f.close()

def log_report(bot, bot_path):
    global bot_started
    to_log = f'\nTime: {int(time.time())}' \
             f'\nLast CCI: {bot.last_cci}' \
             f'\n# Pending operations: {len(bot.pending_operations)}' \
             f'\n# Open operations: {len(bot.open_operations)}' \
             f'\n# Closed operations: {str(bot.closed_operations)}\n\n'
    f = open(f'{bot_path}/log.log', "a")
    f.write(str(to_log))
    f.close()

def register_config(bot, bot_path):
    f = open(f'{bot_path}/log.log', "a")
    to_log = f'CONFIG: \n{str(bot.get_config())}\n'
    f.write(to_log)
    f.close()