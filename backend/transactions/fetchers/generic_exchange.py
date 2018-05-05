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

from backend.utils.utils import get_name_price

from backend.accounts.models import Account
from backend.transactions.models import Transaction
from backend.transactions.models import TransactionUpdateHistoryEntry

from ...utils.utils import exchange_can_batch


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
        # plus add an extra 2 seconds as some exchanges like Bitfinex have varying rate limits
        # and still return rate limit exceeded errors when using the value provided by CCXT
        time.sleep((exchange.rateLimit / 1000) + 2)
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

    total = len(trades)
    num_imports = 0

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
            trx.source_peer = account
            trx.target_peer = account

            date = parser.parse(trx.date)
            timestamp = time.mktime(date.timetuple())

            trx.book_price_btc = get_name_price(
                trx.spent_amount, trx.spent_currency, "BTC", timestamp)
            trx.book_price_eur = get_name_price(
                trx.spent_amount, trx.spent_currency, "EUR", timestamp)
            trx.book_price_fee_btc = get_name_price(
                trx.fee_amount, trx.fee_currency, "BTC", timestamp)
            trx.book_price_fee_eur = get_name_price(
                trx.fee_amount, trx.fee_currency, "EUR", timestamp)
            trx.icon = Transaction.TRX_ICON_EXCHANGE
            trx.save()
            trx.tags.add(account.service_type, Transaction.TRX_TAG_EXCHANGE)
            trx.save()
            num_imports += 1
            time.sleep(0.2)  # avoid hammering the API's

    print("Imported {} trades.".format(num_imports))
    entry: TransactionUpdateHistoryEntry = TransactionUpdateHistoryEntry(
        date=starttime, account=account, fetched_transactions=num_imports)
    entry.save()
