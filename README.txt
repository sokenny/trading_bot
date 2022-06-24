# candle structure
[
    1499040000000,      # Open time
    "0.01634790",       # Open
    "0.80000000",       # High
    "0.01575800",       # Low
    "0.01577100",       # Close
    "148976.11427815",  # Volume
    1499644799999,      # Close time
    "2434.19055334",    # Quote asset volume
    308,                # Number of trades
    "1756.87402397",    # Taker buy base asset volume
    "28.46694368",      # Taker buy quote asset volume
    "17928899.62484339" # Can be ignored
]

# configuration
KLINE_TO_USE_IN_PROD = 5 # Largo de vela (en minutos) que planeamos usar en el escenario real (produccion)
KLINE_INTERVAL = 1 # Largo de vela que vamos a iterar en el backtesting. Puede combinarse con la constante KLINE_TO_USE_IN_PROD para poder ver la evolucion por minuto, de velas de 5 minutos, en un ambito de backtesting
DEFAULT_CCI_LONGITUDE = 20 # Cantidad de velas a ser tenidas en cuenta por el CCI por default
CCI_LONGITUDE = int((KLINE_TO_USE_IN_PROD / KLINE_INTERVAL) * DEFAULT_CCI_LONGITUDE) # Cantidad de velas a ser tenidas en cuenta por el CCI segun las velas que estemos usando en backtesting y que planeemos usar en prod.
PAIR = "ROSEUSDT" # Pair de activos a operar
TRADE_AMOUNT = 100 # Importe a alocar en cada trade (repartido entre las posiciones que se abran)
STOP_LOSS = 1 # Distancia que tiene que recorrer el precio en contra nuestro para completar la posicion e ir a perdida
TAKER_PROFIT = 1.5 # Distancia que tiene que recorrer el precio a favor nuestro para completar la posicion y tomar las ganancias
POSITIONS_STRUCTURE = [{'weight': .15}, {'weight': .15}, {'weight': .25}, {'weight': .35}] # Posiciones a abrir por cada señal de trade con sus respectivos "weights" que representan un porcentaje del importe a tradear
CCI_PEAK = 200 # Valor en el que se activa la señal del CCI
PERIOD = ["20 Jun, 2022", "21 Jun, 2022"] # Periodo de velas a backtestear si se quiere seleccionar un rango especifico, se establecen 2 parametros, ej: "15 Mar, 2022", "6 Apr, 2022". Si es un periodo relativo al dia presente, mandamos un solo item, ej: "1 day ago UTC"
POSITION_EXPIRY_TIME = 3600 # Tiempo en segundos, que deben transcurrir para abortar una posicion "pending" si no logró abrirse
SCORE_FILTER = 0 # Score a superar para que una posicion se abra con "layer: 2"
SCORE_LONGITUDE = 20
START_GAP_PERCENTAGE = 0 # Porcentage base desde el cual se promedia a la baja o a la alta (ej: si esta en 2, un precio de 5 dolares va a empezar a abrir sus posiciones en 5.2)