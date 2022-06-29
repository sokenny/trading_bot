import copy
import config
import backtester
from Bot import Bot

default_config = {"PAIR": config.PAIR, "PERIOD": config.PERIOD, "TRADE_AMOUNT": config.TRADE_AMOUNT, "TAKER_PROFIT": config.TAKER_PROFIT, "STOP_LOSS": config.STOP_LOSS, "POSITIONS_STRUCTURE": config.POSITIONS_STRUCTURE, "KLINE_TO_USE_IN_PROD": config.KLINE_TO_USE_IN_PROD, "KLINE_INTERVAL": config.KLINE_INTERVAL, "CCI_PEAK": config.CCI_PEAK, "POSITION_EXPIRY_TIME": config.POSITION_EXPIRY_TIME, "SCORE_FILTER": config.SCORE_FILTER, "SCORE_LONGITUDE": config.SCORE_LONGITUDE, "START_GAP_PERCENTAGE": config.START_GAP_PERCENTAGE}
config_variants = {"STOP_LOSS": [3,4,5], "TAKER_PROFIT": [1,1.5,2], "START_GAP_PERCENTAGE": [0, 0.5, 1], "CCI_PEAK": [170,200,250]}

def get_config(default_config, custom_parameters):
    new_config = default_config
    for key in custom_parameters.keys():
        new_config[key] = custom_parameters[key]
    return new_config

def get_bots():
    bots = []
    for i1, stop_loss in enumerate(config_variants["STOP_LOSS"]):
        for i2, taker_profit in enumerate(config_variants["TAKER_PROFIT"]):
            for i3, start_gap_percentage in enumerate(config_variants["START_GAP_PERCENTAGE"]):
                for i4, cci_peak in enumerate(config_variants["CCI_PEAK"]):
                    default_copy = copy.deepcopy(default_config)
                    this_config = get_config(default_copy, {"STOP_LOSS": stop_loss, "TAKER_PROFIT": taker_profit, "START_GAP_PERCENTAGE": start_gap_percentage, "CCI_PEAK": cci_peak})
                    bots.append(Bot("sandbox", this_config["PAIR"], this_config["TRADE_AMOUNT"], this_config["TAKER_PROFIT"], this_config["STOP_LOSS"],  this_config["POSITIONS_STRUCTURE"], this_config["KLINE_TO_USE_IN_PROD"], this_config["KLINE_INTERVAL"], this_config["CCI_PEAK"], this_config["POSITION_EXPIRY_TIME"], this_config["SCORE_FILTER"], this_config["SCORE_LONGITUDE"], this_config["START_GAP_PERCENTAGE"]))
    return bots

bots =  get_bots()
results=[]
period = ['10 May, 2021', '11 May, 2021']

for i, bot in enumerate(bots):
    result = backtester.backtest(bot, period, to_return="footer_report")
    results.append([result])

for i in results:
    print(f'\nResult {i}: {results[i]}')