"""Contains all tests for the generic exchange fetcher"""
import random
import pytest
from _pytest.monkeypatch import MonkeyPatch
from mixer.backend.django import mixer
from faker import Faker

import backend.transactions.schema as schema
from backend.accounts.models import Account

from ..importers.livecoin import import_data_livecoin

pytestmark = pytest.mark.django_db


def make_fake_transaction_data():
    # pylint: disable=E1101

    fake = Faker()
    transaction_data = schema.TransactionData()
    transaction_data.date = fake.date_time_between(
        start_date="-30y", end_date="now",
        tzinfo=None).strftime("%d.%m.%Y %H:%m:%s")
    transaction_data.transaction_type = "exchange"
    transaction_data.transaction_type_raw = "Buy"
    transaction_data.spent_currency = fake.cryptocurrency_code()
    transaction_data.spent_amount = random.uniform(1, 20)
    transaction_data.source_peer = 1
    transaction_data.acquired_currency = fake.cryptocurrency_code()
    transaction_data.acquired_amount = random.uniform(0.001, 10)
    transaction_data.target_peer = 1
    transaction_data.fee_currency = transaction_data.spent_currency
    transaction_data.fee_amount = random.uniform(0.000001, 0.001)
    transaction_data.tags = ["tag1", "tag2"]
    return transaction_data


def test_import_csv_livecoin(monkeypatch: MonkeyPatch):
    user = mixer.blend("auth.User")
    livecoin: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="livecoin")

    data = schema.ImportTransactionInput()
    data.service_type = "livecoin"
    data.import_mechanism = "csv"
    data.transactions = [
        make_fake_transaction_data(),
        make_fake_transaction_data()
    ]

    res = import_data_livecoin(data, user)
    assert len(res) == 2
