import copy
import config
import backtester
import sys
import io
from Bot import Bot

def backtest(configs):

    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    default_config = {"PAIR": config.PAIR, "PERIOD": config.PERIOD, "TRADE_AMOUNT": config.TRADE_AMOUNT, "TAKE_PROFIT": config.TAKE_PROFIT, "STOP_LOSS": config.STOP_LOSS, "POSITION_STRUCTURE": config.POSITION_STRUCTURE, "KLINE_TO_USE_IN_PROD": config.KLINE_TO_USE_IN_PROD, "KLINE_INTERVAL": config.KLINE_INTERVAL, "CCI_PEAK": config.CCI_PEAK, "OPERATION_EXPIRY_TIME": config.OPERATION_EXPIRY_TIME, "SCORE_FILTER": config.SCORE_FILTER, "SCORE_LONGITUDE": config.SCORE_LONGITUDE, "START_GAP_PERCENTAGE": config.START_GAP_PERCENTAGE}

    def get_config(default_config, custom_parameters):
        new_config = default_config
        for key in custom_parameters.keys():
            new_config[key] = custom_parameters[key]
        return new_config

    def get_bots():
        bots = []
        for i1, stop_loss in enumerate(configs["STOP_LOSS"]):
            for i2, take_profit in enumerate(configs["TAKE_PROFIT"]):
                for i3, start_gap_percentage in enumerate(configs["START_GAP_PERCENTAGE"]):
                    for i4, cci_peak in enumerate(configs["CCI_PEAK"]):
                        for i5, position_structure in enumerate(configs["POSITION_STRUCTURE"]):
                            default_copy = copy.deepcopy(default_config)
                            this_config = get_config(default_copy, {"PAIR": configs["PAIR"], "OPERATION_EXPIRY_TIME": configs["OPERATION_EXPIRY_TIME"], "STOP_LOSS": stop_loss, "TAKE_PROFIT": take_profit, "START_GAP_PERCENTAGE": start_gap_percentage, "CCI_PEAK": cci_peak, "POSITION_STRUCTURE": position_structure})
                            bots.append(Bot("sandbox", this_config["PAIR"], this_config["TRADE_AMOUNT"], this_config["TAKE_PROFIT"], this_config["STOP_LOSS"],  this_config["POSITION_STRUCTURE"], this_config["KLINE_TO_USE_IN_PROD"], this_config["KLINE_INTERVAL"], this_config["CCI_PEAK"], this_config["OPERATION_EXPIRY_TIME"], this_config["SCORE_FILTER"], this_config["SCORE_LONGITUDE"], this_config["START_GAP_PERCENTAGE"]))
        return bots

    bots =  get_bots()
    results=[]
    period = configs["PERIOD"]
    candles = None
    cummulative_score = 0
    print("# of bots created: ", len(bots))

    for i, bot in enumerate(bots):
        if(candles == None):
            candles = bot.get_candle_sticks(period)
        result = backtester.backtest(bot, candles)[1]
        print(f'BOT {i}')
        results.append(result)
        cummulative_score += result["layer_1_score"]

    print("\n\nAVG BOTS SCORE: ", cummulative_score / len(bots))

    sys.stdout = old_stdout
    whole_print_output = buffer.getvalue()

    return [whole_print_output]