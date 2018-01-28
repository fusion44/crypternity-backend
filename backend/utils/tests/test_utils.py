import pytest

from ..utils import exchange_can_batch


def test_exchange_can_batch():
    assert exchange_can_batch("binance") == False
    assert exchange_can_batch("cryptopia") == True