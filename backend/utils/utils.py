"""Contains various utility functions"""

import time
import cryptocompare as cc
from diskcache import FanoutCache


def exchange_can_batch(exchange: str) -> bool:
    # For some exchanges it is impossible to get all trades for
    # an account and we have to fetch each symbol individually.
    # Binance, for example. Cryptopia does not have this problem.
    if exchange == "binance":
        return False
    elif exchange == "bitfinex":
        return False

    return True


# use a simple cache mechanism to avoid hammering the API
CACHE = FanoutCache('/tmp/diskcache/fanoutcache')


def get_name_price(amount: float,
                   base: str,
                   target: str,
                   timestamp: float = time.time()) -> float:
    """
    Calculated the price of one name in another name.
    Returns a float with the converted value as a decimal.Decimal

    Keyword arguments:
    amount -- amount to convert
    base -- name to convert from
    target -- name to convert to
    date -- historic date as a Unix Timestamp (default: time.time())
    """
    key = base + target + str(timestamp)
    request_res = CACHE.get(key, None)
    if request_res is None:
        request_res = cc.get_historical_price(base, target, timestamp)
        CACHE.add(key, request_res)

    val = request_res[base][target]

    return amount * val
