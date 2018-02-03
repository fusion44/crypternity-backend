import pytest
from django.utils.timezone import now
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from backend.accounts.models import Account
from backend.transactions.models import Transaction
from backend.transactions.models import TransactionUpdateHistoryEntry

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db

# Great introduction to TDD with Python + Django:
# https://www.youtube.com/watch?v=41ek3VNx_6Q


def test_transaction_creation():
    obj = mixer.blend("transactions.Transaction")
    assert obj.pk > 0, "Should create an Transaction instance"


def test_transaction_str_func():
    name = "50.0 BTC => 150.01 ETH ==> 300.0 EUR"
    t: Transaction = mixer.blend(
        "transactions.Transaction",
        spent_amount=50.0000,
        spent_currency="BTC",
        aquired_amount=150.0100,
        aquired_currency="ETH",
        book_price_eur=300)

    assert t.__str__() == name, "Should be the transaction's name"


def test_transaction_history_entry_creation():
    account: Account = mixer.blend("accounts.Account")
    obj = mixer.blend(
        "transactions.TransactionUpdateHistoryEntry", account=account)
    assert obj.pk > 0, "Should create an Transaction instance"


def test_transaction_history_entry_str_func():
    account: Account = mixer.blend("accounts.Account")

    datea = now()
    dateb = now()

    entrya: TransactionUpdateHistoryEntry = mixer.blend(
        "transactions.TransactionUpdateHistoryEntry",
        date=datea,
        account=account,
        fetched_transactions=3)
    entryb: TransactionUpdateHistoryEntry = mixer.blend(
        "transactions.TransactionUpdateHistoryEntry",
        date=dateb,
        account=account,
        fetched_transactions=6)

    namea = "{} {} {}".format(1, datea, 3)
    nameb = "{} {} {}".format(1, dateb, 6)

    assert entrya.__str__() == namea
    assert entryb.__str__() == nameb
