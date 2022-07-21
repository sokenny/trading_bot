import backtester
import multibacktester
import config as default_config
from classes.Bot import Bot

def get_single_backtest(config):
    bot = Bot(mode="sandbox", pair=config['PAIR'], take_profit=config['TAKE_PROFIT'], stop_loss=config['STOP_LOSS'], position_structure=eval(config['POSITION_STRUCTURE']), cci_peak=config['CCI_PEAK'], operation_expiry_time=config['OPERATION_EXPIRY_TIME'], start_gap_percentage=config['START_GAP_PERCENTAGE'], max_weight_allocation=config["MAX_WEIGHT_ALLOCATION"], kline_to_use_in_prod=default_config.KLINE_TO_USE_IN_PROD, kline_interval=default_config.KLINE_INTERVAL, trade_amount=default_config.TRADE_AMOUNT)
    candles = bot.get_candle_sticks(eval(config['PERIOD']))
    backtest_log = backtester.backtest(bot, candles)
    return backtest_log

def get_multi_backtest(configs):
    parsed_configs = {}
    to_not_eval = ["PAIR", "OPERATION_EXPIRY_TIME", "MAX_WEIGHT_ALLOCATION"]
    for key in configs.keys():
        parsed_configs[key] = eval(configs[key]) if key not in to_not_eval else configs[key]
    backtest_log = multibacktester.backtest(parsed_configs)[0]
    return backtest_log