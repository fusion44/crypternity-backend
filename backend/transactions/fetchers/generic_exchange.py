"""
Contains all functions related to importing transactions
from exchanges supported by the ccxt library
"""

import ccxt
import time
from datetime import datetime, timezone
from django.utils.timezone import now
from requests.exceptions import ReadTimeout
from dateutil import parser
from django.db.models import QuerySet

import cryptocompare

from backend.accounts.models import Account
from backend.transactions.models import Transaction
from backend.transactions.models import TransactionUpdateHistoryEntry

from ...utils.utils import exchange_can_batch

CACHE = {}


def fetch_trades_unbatched(exchange: ccxt.Exchange):
    """
    Some exchanges like Binance don't support fetching all trades at
    once and need to fetch per trading pair (market).
    """
    markets = exchange.load_markets()
    trades = []
    for market in markets:
        try:
            trades += exchange.fetch_my_trades(market)
        except ReadTimeout as err:
            print(err)
            continue

        # exchange.rateLimit is milliseconds but time.sleep expects seconds
        time.sleep(exchange.rateLimit / 1000)
    return trades


def update_exchange_trx_generic(account: Account):
    """
    Fetches all trades and if older than last check imports to database
    """
    exchange: ccxt.Exchange = None
    starttime: datetime = now()

    if hasattr(ccxt, account.service_type):
        exchange: ccxt.Exchange = getattr(ccxt, account.service_type)({
            "api_key":
            account.api_key,
            "secret":
            account.api_secret
        })
    else:
        print("nope")

    last_update_query: QuerySet = TransactionUpdateHistoryEntry.objects.filter(
        account=account).order_by('-date')
    latest_update = datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc)

    if last_update_query.count():
        latest_update = last_update_query[:1][0].date

    transactions = []
    trades = []
    if exchange_can_batch(account.service_type):
        trades = exchange.fetch_my_trades()
    else:
        trades = fetch_trades_unbatched(exchange)

    if trades:
        for trade in trades:
            # print(trade["symbol"] + " " + trade["datetime"])

            trade_date = parser.parse(trade["datetime"])
            if trade_date <= latest_update:
                print("skiping ", trade["symbol"] + " " + trade["datetime"])
                continue

            split = trade["symbol"].split("/")

            trx = Transaction()
            if trade["side"] == "buy":
                trx.spent_amount = trade["cost"]
                trx.spent_currency = split[1]

                trx.acquired_amount = trade["amount"]
                trx.acquired_currency = split[0]
            elif trade["side"] == "sell":
                trx.spent_amount = trade["amount"]
                trx.spent_currency = split[0]

                trx.acquired_amount = trade["cost"]
                trx.acquired_currency = split[1]

            trx.fee_amount = trade["fee"]["cost"]
            trx.fee_currency = trade["fee"]["currency"]

            trx.date = trade["datetime"]
            trx.owner = account.owner
            trx.source_account = account
            trx.target_account = account

            date = parser.parse(trx.date)
            key = trx.spent_currency + "-" + str(date.year) + "-" + str(
                date.month) + "-" + str(date.day)
            key_fee = trx.fee_currency + "-" + str(date.year) + "-" + str(
                date.month) + "-" + str(date.day)

            book_price_btc = book_price_eur = book_price_fee_btc = book_price_fee_eur = None

            if key in CACHE:
                book_price_btc = CACHE[key]["price_btc"]
                book_price_eur = CACHE[key]["price_eur"]
            else:
                book_price_btc = cryptocompare.get_historical_price(
                    trx.spent_currency, "BTC", date)[trx.spent_currency]["BTC"]
                book_price_eur = cryptocompare.get_historical_price(
                    trx.spent_currency, "EUR", date)[trx.spent_currency]["EUR"]
                CACHE[key] = {
                    "price_btc": book_price_btc,
                    "price_eur": book_price_eur
                }

            if key_fee in CACHE:
                book_price_fee_btc = CACHE[key_fee]["price_btc"]
                book_price_fee_eur = CACHE[key_fee]["price_eur"]
            else:
                book_price_fee_btc = cryptocompare.get_historical_price(
                    trx.fee_currency, "BTC", date)[trx.fee_currency]["BTC"]
                book_price_fee_eur = cryptocompare.get_historical_price(
                    trx.fee_currency, "EUR", date)[trx.fee_currency]["EUR"]
                CACHE[key_fee] = {
                    "price_btc": book_price_fee_btc,
                    "price_eur": book_price_fee_eur
                }

            trx.book_price_btc = trx.spent_amount * book_price_btc
            trx.book_price_eur = trx.spent_amount * book_price_eur
            trx.book_price_fee_btc = trx.fee_amount * book_price_fee_btc
            trx.book_price_fee_eur = trx.fee_amount * book_price_fee_eur

            transactions.append(trx)
            time.sleep(0.2)  # avoid hammering the API's
        Transaction.objects.bulk_create(transactions)
    entry: TransactionUpdateHistoryEntry = TransactionUpdateHistoryEntry(
        date=starttime,
        account=account,
        fetched_transactions=len(transactions))
    entry.save()
