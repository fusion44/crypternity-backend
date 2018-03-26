"""Contains all functions related to importing Coinbase data"""

import json
import time
from datetime import datetime, timezone
from collections import namedtuple
from dateutil import parser
from django.utils.timezone import now

from coinbase.wallet.client import Client

from backend.transactions.models import Transaction, TransactionUpdateHistoryEntry

from backend.accounts.models import Account
from backend.utils.utils import get_name_price


def update_coinbase_trx(account: Account):
    """Synchronizes all transactions from Coinbase"""
    last_update_query = TransactionUpdateHistoryEntry.objects.filter(
        account=account).order_by('-date')
    latest_update = datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc)
    if last_update_query.count():
        latest_update = last_update_query[:1][0].date

    client: Client = Client(account.api_key, account.api_secret)
    cb_accounts = client.get_accounts()

    new_transactions = []

    for cb_account in cb_accounts["data"]:
        if cb_account["type"] == "fiat":
            continue

        buy_sell_list = []
        buy_sell_list.extend(client.get_buys(cb_account["id"])["data"])
        buy_sell_list.extend(client.get_sells(cb_account["id"])["data"])

        if buy_sell_list:
            for trx in buy_sell_list:
                new_trx: Transaction = Transaction()

                new_trx.date = trx["created_at"]
                date = parser.parse(trx["created_at"])

                if date <= latest_update:
                    continue

                timestamp = time.mktime(date.timetuple())
                if trx["resource"] == "buy":
                    new_trx.acquired_amount = float(trx["amount"]["amount"])
                    new_trx.acquired_currency = trx["amount"]["currency"]

                    new_trx.spent_amount = float(trx["total"]["amount"])
                    new_trx.spent_currency = trx["total"]["currency"]
                elif trx["resource"] == "sell":
                    new_trx.acquired_amount = float(trx["total"]["amount"])
                    new_trx.acquired_currency = trx["total"]["currency"]

                    new_trx.spent_amount = float(trx["amount"]["amount"])
                    new_trx.spent_currency = trx["amount"]["currency"]
                else:
                    print("not a buy or sell, skipping.")
                    continue

                if new_trx.acquired_currency == "BTC":
                    new_trx.book_price_btc = new_trx.acquired_amount
                else:
                    new_trx.book_price_btc = get_name_price(
                        new_trx.acquired_amount, new_trx.acquired_currency,
                        "BTC", timestamp)

                new_trx.book_price_eur = float(trx["total"]["amount"])
                new_trx.book_price_btc = get_name_price(
                    new_trx.book_price_eur, "EUR", "BTC", timestamp)

                new_trx.fee_amount = new_trx.book_price_fee_eur = float(
                    trx["fees"][0]["amount"]["amount"])
                new_trx.fee_currency = trx["fees"][0]["amount"]["currency"]
                new_trx.book_price_fee_btc = get_name_price(
                    new_trx.book_price_fee_eur, "EUR", "BTC", timestamp)

                new_trx.owner = account.owner
                new_trx.source_peer = account
                new_trx.target_peer = account
                new_transactions.append(new_trx)
                time.sleep(2)  # sleep to prevent api spam

    Transaction.objects.bulk_create(new_transactions)
    entry: TransactionUpdateHistoryEntry = TransactionUpdateHistoryEntry(
        date=now(),
        account=account,
        fetched_transactions=len(new_transactions))
    entry.save()

    print("Imported {} transactions".format(len(new_transactions)))
