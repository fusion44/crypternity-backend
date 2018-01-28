import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from backend.transactions.models import Transaction
from .. import schema

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

    assert t.__str__() == name, "Should be the accounts's name"