"""Livecoin exchange importer functions"""
import time

from backend.utils.utils import get_name_price
from backend.transactions.models import Transaction
import arrow
from backend.accounts.models import Peer


def import_data_livecoin(data, user):
    """Import data from a CSV file exported from Livecoin

    Arguments:
        data {object} -- Object with the Livecoin data
        user {user} -- Current logged in User

    Returns:
        Transaction -- List with the imported transactions
    """

    transactions = []
    peer_cache = {}
    for trx_input in data.transactions:  # type: TransactionData
        if trx_input.transaction_type_raw == "Deposit":
            continue

        trx = Transaction()
        date = arrow.get(trx_input.date, "DD.MM.YYYY HH:mm:ss")
        timestamp = date.timestamp
        trx.date = date.datetime
        trx.owner = user

        # calculate book price by spent amount
        book_price_ok = False
        if trx_input.spent_amount > 0 and trx_input.spent_currency is not "":
            trx.spent_amount = trx_input.spent_amount
            trx.spent_currency = trx_input.spent_currency

            trx.book_price_btc = get_name_price(
                trx.spent_amount, trx.spent_currency, "BTC", timestamp)
            trx.book_price_eur = get_name_price(
                trx.spent_amount, trx.spent_currency, "EUR", timestamp)
            book_price_ok = True

        if trx_input.acquired_amount > 0 and trx_input.acquired_currency is not "":
            trx.acquired_amount = trx_input.acquired_amount
            trx.acquired_currency = trx_input.acquired_currency
            if not book_price_ok:
                trx.book_price_btc = get_name_price(trx.acquired_amount,
                                                    trx.acquired_currency,
                                                    "BTC", timestamp)
                trx.book_price_eur = get_name_price(trx.acquired_amount,
                                                    trx.acquired_currency,
                                                    "EUR", timestamp)
        # if trx_input.source_peer not in trx
        trx.source_peer = Peer(pk=trx_input.source_peer)
        trx.target_peer = Peer(pk=trx_input.target_peer)

        if trx_input.fee_amount > 0:
            trx.fee_amount = trx_input.fee_amount
            trx.fee_currency = trx_input.fee_currency
            trx.book_price_fee_btc = get_name_price(
                trx.fee_amount, trx.fee_currency, "BTC", timestamp)
            trx.book_price_fee_eur = get_name_price(
                trx.fee_amount, trx.fee_currency, "EUR", timestamp)

        if trx_input.transaction_type == "exchange":
            trx.icon = Transaction.TRX_ICON_EXCHANGE
            trx.save()
            trx.tags.add(data.service_type, data.import_mechanism,
                         Transaction.TRX_TAG_EXCHANGE)
        elif trx_input.transaction_type == "income":
            trx.icon = Transaction.TRX_ICON_INCOME
            trx.save()
            trx.tags.add(data.service_type, data.import_mechanism,
                         Transaction.TRX_TAG_INCOME)
        elif trx_input.transaction_type == "transfer":
            trx.icon = Transaction.TRX_ICON_TRANSFER
            trx.save()
            trx.tags.add(data.service_type, data.import_mechanism,
                         Transaction.TRX_TAG_TRANSFER)
        else:
            trx.icon = Transaction.TRX_ICON_WARNING
            trx.save()
            trx.tags.add(data.service_type, data.import_mechanism,
                         Transaction.TRX_TAG_WARNING)

        if trx_input.tags:
            for tag in trx_input.tags:
                trx.tags.add(tag)
        trx.save()
        transactions.append(trx)
    return transactions
