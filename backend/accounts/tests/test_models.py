import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db

# Great introduction to TDD with Python + Django:
# https://www.youtube.com/watch?v=41ek3VNx_6Q


def test_peer_str_func():
    name = "test123"
    obj = mixer.blend("accounts.peer", name=name)
    assert obj.__str__() == "[Peer] {}".format(
        name), "Should be the peer's name"


def test_address_str_func():
    address = "test123"
    obj = mixer.blend("accounts.Address", address=address)
    symbol = obj.coin.symbol
    assert obj.__str__() == "{}:{}".format(symbol, address)


def test_account_creation():
    obj = mixer.blend("accounts.Account")
    assert obj.pk > 0, "Should create an Account instance"


def test_account_str_func():
    name = "test123"
    obj = mixer.blend("accounts.Account", name=name)
    assert obj.__str__() == "[Account] {}".format(
        name), "Should be the accounts's name"
