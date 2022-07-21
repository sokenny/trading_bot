from live import operate
from classes.Bot import Bot

bot = Bot(
    id="juanito-trader",
    mode="live-trade",
    pair="ROSEUSDT",
    take_profit=1,
    stop_loss=25,
    position_structure=[{'weight': .5}, {'weight': .5}],
    cci_peak=10,
    operation_expiry_time=2500,
    start_gap_percentage=0,
    max_weight_allocation=1,
    trade_amount=20,
    kline_interval=5,
    kline_to_use_in_prod=5
)

operate(bot, trade_every=30, log_every=60)