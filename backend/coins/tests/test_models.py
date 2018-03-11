'''Contains all model tests for this application'''
import pytest
from mixer.backend.django import mixer
from backend.coins.models import Coin

pytestmark = pytest.mark.django_db


def test_coin_creation():
    '''Test Coin object creation'''
    obj = mixer.blend("coins.Coin")
    assert obj.pk > 0, "Should create a Coin instance"


def test_coin_str_func():
    '''Test Coin object string function'''
    name = "BTC - Bitcoin"
    coin: Coin = mixer.blend(
        "coins.Coin", cc_id=50, symbol="BTC", full_name="Bitcoin")

    assert coin.__str__() == name, "Should be the coins's name"
