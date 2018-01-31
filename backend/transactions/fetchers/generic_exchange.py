import ccxt
import time
import datetime
from requests.exceptions import ReadTimeout
from dateutil import parser

import cryptocompare

from backend.accounts.models import Account
from backend.transactions.models import Transaction

from ...utils.utils import exchange_can_batch

cache = {}


def fetch_trades_unbatched(exchange: ccxt.Exchange):
    markets = exchange.load_markets()
    trades = []
    for market in markets:
        try:
            trades += exchange.fetch_my_trades(market)
        except ReadTimeout as err:
            print(err)
            continue

        # exchange.rateLimit is millisecons but time.sleep expects seconds
        time.sleep(exchange.rateLimit / 1000)
    return trades


def update_exchange_tx_generic(account: Account):
    exchange: ccxt.Exchange = None

    if hasattr(ccxt, account.service_type):
        exchange: ccxt.Exchange = getattr(ccxt, account.service_type)({
            "api_key":
            account.api_key,
            "secret":
            account.api_secret
        })
    else:
        print("nope")

    transactions = []
    trades = []
    if exchange_can_batch(account.service_type):
        trades = exchange.fetch_my_trades()
    else:
        trades = fetch_trades_unbatched(exchange)

    if trades:
        for trade in trades:
            # print(trade["symbol"] + " " + trade["datetime"])

            split = trade["symbol"].split("/")

            t = Transaction()
            if trade["side"] == "buy":
                t.spent_amount = trade["cost"]
                t.spent_currency = split[1]

                t.aquired_amount = trade["amount"]
                t.aquired_currency = split[0]
            elif trade["side"] == "sell":
                t.spent_amount = trade["amount"]
                t.spent_currency = split[0]

                t.aquired_amount = trade["cost"]
                t.aquired_currency = split[1]

            t.fee_amount = trade["fee"]["cost"]
            t.fee_currency = trade["fee"]["currency"]

            t.date = trade["datetime"]
            t.owner = account.owner
            t.source_account = account
            t.target_account = account

            date = parser.parse(t.date)
            key = t.spent_currency + "-" + str(date.year) + "-" + str(
                date.month) + "-" + str(date.day)
            key_fee = t.fee_currency + "-" + str(date.year) + "-" + str(
                date.month) + "-" + str(date.day)

            book_price_btc = book_price_eur = book_price_fee_btc = book_price_fee_eur = None

            if key in cache:
                book_price_btc = cache[key]["price_btc"]
                book_price_eur = cache[key]["price_eur"]
            else:
                book_price_btc = cryptocompare.get_historical_price(
                    t.spent_currency, "BTC", date)[t.spent_currency]["BTC"]
                book_price_eur = cryptocompare.get_historical_price(
                    t.spent_currency, "EUR", date)[t.spent_currency]["EUR"]
                cache[key] = {
                    "price_btc": book_price_btc,
                    "price_eur": book_price_eur
                }

            if key_fee in cache:
                book_price_fee_btc = cache[key_fee]["price_btc"]
                book_price_fee_eur = cache[key_fee]["price_eur"]
            else:
                book_price_fee_btc = cryptocompare.get_historical_price(
                    t.fee_currency, "BTC", date)[t.fee_currency]["BTC"]
                book_price_fee_eur = cryptocompare.get_historical_price(
                    t.fee_currency, "EUR", date)[t.fee_currency]["EUR"]
                cache[key_fee] = {
                    "price_btc": book_price_fee_btc,
                    "price_eur": book_price_fee_eur
                }

            t.book_price_btc = t.spent_amount * book_price_btc
            t.book_price_eur = t.spent_amount * book_price_eur
            t.book_price_fee_btc = t.fee_amount * book_price_fee_btc
            t.book_price_fee_eur = t.fee_amount * book_price_fee_eur

            transactions.append(t)
            time.sleep(0.2)  # avoid hammering the API's
        Transaction.objects.bulk_create(transactions)
