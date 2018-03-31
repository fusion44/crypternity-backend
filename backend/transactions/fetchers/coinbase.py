"""Contains all functions related to importing Coinbase data"""

import json
import time
from requests.sessions import Session
from datetime import datetime, timezone
from collections import namedtuple
from dateutil import parser
from django.utils.timezone import now

from coinbase.wallet.client import Client, APIObject

from backend.transactions.models import Transaction, TransactionUpdateHistoryEntry

from backend.accounts.models import Account
from backend.utils.utils import get_name_price


def process_send(cb_trx, timestamp: int, account: Account) -> Transaction:
    """Process all Coinbase send transactions

    Arguments:
        cb_trx {APIObject} -- the coinbase transaction to import
        timestamp {float} -- timestamp of last import from coinbase
        account {Account} -- the account this transaction originates from

    Returns:
        Transaction -- a Transaction object
    """

    new_trx = Transaction()
    new_trx.date = cb_trx["created_at"]

    # minus on coinbase (source peer)
    new_trx.spent_amount = abs(float(cb_trx["amount"]["amount"]))
    new_trx.spent_currency = cb_trx["amount"]["currency"]

    network = cb_trx["network"]

    if network["status"] == "off_blockchain":
        # could be a refferal bonus from Coinbase
        new_trx.acquired_amount = abs(float(cb_trx["amount"]["amount"]))
        new_trx.acquired_currency = cb_trx["amount"]["currency"]

        # a refferal bonus has no fee, so use defaults from model
    else:
        # amount received on target peer (spent amount with network fees deducted)
        new_trx.acquired_amount = abs(
            float(network["transaction_amount"]["amount"]))
        new_trx.acquired_currency = network["transaction_amount"]["currency"]

        # network fee for this transaction
        new_trx.fee_amount = abs(float(network["transaction_fee"]["amount"]))
        new_trx.fee_currency = network["transaction_fee"]["currency"]

        new_trx.book_price_fee_eur = get_name_price(
            new_trx.fee_amount, new_trx.fee_currency, "EUR", timestamp)
        new_trx.book_price_fee_btc = get_name_price(
            new_trx.fee_amount, new_trx.fee_currency, "BTC", timestamp)

    # calculate book prices
    # number might be negative, make absolute
    new_trx.book_price_eur = abs(float(cb_trx["native_amount"]["amount"]))
    new_trx.book_price_btc = get_name_price(
        new_trx.spent_amount, new_trx.spent_currency, "BTC", timestamp)

    new_trx.owner = account.owner
    new_trx.source_peer = account

    # TODO: get target address and query database for known addresses
    # If it exists, get the parent Peer for this address and set as target
    # new_trx.target_peer = None
    return new_trx


def process_buy_sell(cb_trx, timestamp, account: Account) -> Transaction:
    """Process all Coinbase buys and sells

    Arguments:
        cb_trx {APIObject} -- the coinbase transaction to import
        timestamp {float} -- timestamp of last import from coinbase
        account {Account} -- the account this buy or sell originates from

    Raises:
            ValueError -- when resource is not "buy" or "sell"

    Returns:
        Transaction -- a Transaction object
    """

    new_trx: Transaction = Transaction()
    new_trx.date = cb_trx["created_at"]

    if cb_trx["resource"] == "buy":
        new_trx.acquired_amount = float(cb_trx["amount"]["amount"])
        new_trx.acquired_currency = cb_trx["amount"]["currency"]

        new_trx.spent_amount = float(cb_trx["total"]["amount"])
        new_trx.spent_currency = cb_trx["total"]["currency"]
    elif cb_trx["resource"] == "sell":
        new_trx.acquired_amount = float(cb_trx["total"]["amount"])
        new_trx.acquired_currency = cb_trx["total"]["currency"]

        new_trx.spent_amount = float(cb_trx["amount"]["amount"])
        new_trx.spent_currency = cb_trx["amount"]["currency"]
    else:
        raise ValueError("Type of transaction must either be buy or sell")

    if new_trx.acquired_currency == "BTC":
        new_trx.book_price_btc = new_trx.acquired_amount
    else:
        new_trx.book_price_btc = get_name_price(new_trx.acquired_amount,
                                                new_trx.acquired_currency,
                                                "BTC", timestamp)

    new_trx.book_price_eur = abs(float(cb_trx["total"]["amount"]))
    new_trx.book_price_btc = get_name_price(new_trx.book_price_eur, "EUR",
                                            "BTC", timestamp)

    new_trx.fee_amount = new_trx.book_price_fee_eur = abs(
        float(cb_trx["fees"][0]["amount"]["amount"]))
    new_trx.fee_currency = cb_trx["fees"][0]["amount"]["currency"]
    new_trx.book_price_fee_btc = get_name_price(new_trx.book_price_fee_eur,
                                                "EUR", "BTC", timestamp)

    new_trx.owner = account.owner
    new_trx.source_peer = account
    new_trx.target_peer = account
    return new_trx


def fetch_from_cb(what_to_fetch: str, cb_client: Client,
                  cb_account_id: str) -> []:
    """Fetch the specified data from Coinbase

    buys and sells: Merchant buyouts like FIAT -> BTC etc.
    transfers: Coin transfers from Coinbase to a wallet address

    Arguments:
        what_to_fetch {str} -- either "buys", "sells" or "transfers"
        cb_client {Client} -- coinbase client object
        cb_account_id {str} -- coinbase account id to use

    Returns:
        [] -- a list with the APIObjects from Coinbase
    """

    the_list = []
    data = dict()
    next_uri = ""
    while next_uri != None:
        if what_to_fetch == "buys":
            ret = cb_client.get_buys(cb_account_id, **data)
        elif what_to_fetch == "sells":
            ret = cb_client.get_sells(cb_account_id, **data)
        elif what_to_fetch == "transfers":
            ret = cb_client.get_transactions(cb_account_id, **data)

        print(ret)

        the_list.extend(ret["data"])
        next_uri = ret["pagination"]["next_uri"]
        if next_uri != None:
            data["starting_after"] = ret["data"][-1]["id"]
    return the_list


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

        # Unfortunately, the coinbase API only returns buys and sells
        # without the fee data when fetching through get_transactions.
        # For that reason we still have to use client.get_buys() and client.get_sells()
        # and cannot use the data returned from client.get_transactions()
        cb_transactions = fetch_from_cb("transfers", client, cb_account["id"])
        for cb_trx in cb_transactions:
            if cb_trx["type"] == "send":
                date = parser.parse(cb_trx["created_at"])
                if date <= latest_update:
                    continue
                timestamp = time.mktime(date.timetuple())

                new_transactions.append(
                    process_send(cb_trx, timestamp, account))
                time.sleep(1)  # sleep to prevent api spam

        buy_sell_list = []
        buy_sell_list.extend(fetch_from_cb("buys", client, cb_account["id"]))
        buy_sell_list.extend(fetch_from_cb("sells", client, cb_account["id"]))

        for buy_sell in buy_sell_list:
            if buy_sell["resource"] == "buy" or buy_sell["resource"] == "sell":
                if buy_sell["status"] != "completed":
                    # Skip everything not completed.
                    # This could be created or canceled.
                    continue

                date = parser.parse(buy_sell["created_at"])
                if date <= latest_update:
                    continue
                timestamp = time.mktime(date.timetuple())
                new_transactions.append(
                    process_buy_sell(buy_sell, timestamp, account))
                time.sleep(1)  # sleep to prevent api spam

    Transaction.objects.bulk_create(new_transactions)
    entry: TransactionUpdateHistoryEntry = TransactionUpdateHistoryEntry(
        date=now(),
        account=account,
        fetched_transactions=len(new_transactions))
    entry.save()

    print("Imported {} transactions".format(len(new_transactions)))
