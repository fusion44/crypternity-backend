"""Contains all tests for the generic exchange fetcher"""
import random
import pytest
from _pytest.monkeypatch import MonkeyPatch
from mixer.backend.django import mixer
from faker import Faker
import cryptocompare

import backend.transactions.schema as schema
from backend.accounts.models import Account

from backend.transactions.importers.livecoin import import_data_livecoin

pytestmark = pytest.mark.django_db


def make_fake_transaction_data(date=None,
                               transaction_type=None,
                               transaction_type_raw=None,
                               spent_currency=None,
                               spent_amount=None,
                               source_peer=None,
                               acquired_currency=None,
                               acquired_amount=None,
                               target_peer=None,
                               fee_currency=None,
                               fee_amount=None,
                               tags=None):
    """Generate a fake transaction data input. Mixer is unable to blend these"""
    # pylint: disable=E1101

    fake = Faker()
    transaction_data = schema.TransactionData()
    transaction_data.date = date or fake.date_time_between(
        start_date="-30y", end_date="now",
        tzinfo=None).strftime("%d.%m.%Y %H:%m:%S")
    transaction_data.transaction_type = transaction_type or "exchange"
    transaction_data.transaction_type_raw = transaction_type_raw or "Buy"
    transaction_data.spent_currency = \
        spent_currency or fake.cryptocurrency_code()
    transaction_data.spent_amount = spent_amount or random.uniform(1, 20)
    transaction_data.source_peer = source_peer or 1
    transaction_data.acquired_currency = \
        acquired_currency or fake.cryptocurrency_code()
    transaction_data.acquired_amount = \
        acquired_amount or random.uniform(0.001, 10)
    transaction_data.target_peer = target_peer or 1
    transaction_data.fee_currency = fee_currency or transaction_data.spent_currency
    transaction_data.fee_amount = fee_amount or random.uniform(0.000001, 0.001)
    transaction_data.tags = tags or ["tag1", "tag2"]
    return transaction_data


def new_get_historical_price(base, target, date):
    """Fake crypto compare API"""
    return {base: {target: 10}}


def test_import_csv_livecoin(monkeypatch: MonkeyPatch):
    user = mixer.blend("auth.User")
    livecoin: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="livecoin")

    monkeypatch.setattr(cryptocompare, "get_historical_price",
                        new_get_historical_price)

    data = schema.ImportTransactionInput()
    data.service_type = "livecoin"
    data.import_mechanism = "csv"
    data.transactions = [
        make_fake_transaction_data(),
        make_fake_transaction_data(),
        make_fake_transaction_data(
            transaction_type_raw="Deposit"),  # should be skipped
        make_fake_transaction_data(
            acquired_amount=10, acquired_currency="ETH"),
        make_fake_transaction_data(transaction_type="income"),
        make_fake_transaction_data(transaction_type="transfer"),
        make_fake_transaction_data(
            spent_amount=0,
            spent_currency="h",
            acquired_amount=0.01,
            acquired_currency="BTC",
            transaction_type="income"),
        make_fake_transaction_data(transaction_type="unkown type")
    ]

    res = import_data_livecoin(data, user)
    assert len(res) == 7
