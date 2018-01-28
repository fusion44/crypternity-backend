def exchange_can_batch(exchange: str) -> bool:
    # For some exchanges it is impossible to get all trades for
    # an account and we have to fetch each symbol individually.
    # Binance, for example. Cryptopia does not have this problem.
    if exchange == "binance":
        return False

    return True
