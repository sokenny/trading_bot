from live import operate
from classes.Bot import Bot

bot = Bot(
    id="juanito",
    mode="live-test",
    pair="ROSEUSDT",
    take_profit=3,
    stop_loss=25,
    position_structure=[{'weight': .5}, {'weight': .5}],
    cci_peak=50,
    operation_expiry_time=2500,
    start_gap_percentage=2,
    max_weight_allocation=2,
    trade_amount=100,
    kline_interval=5,
    kline_to_use_in_prod=5
)

operate(bot, trade_every=60, log_every=1800)