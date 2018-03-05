"""Contains all tests for the utility functions"""

import pytest
from _pytest.monkeypatch import MonkeyPatch
import cryptocompare

from ..utils import exchange_can_batch, get_name_price


def test_exchange_can_batch():
    assert exchange_can_batch("binance") == False
    assert exchange_can_batch("cryptopia") == True


pytestmark = pytest.mark.django_db


def new_get_historical_price(base, target, timestamp):
    """
    Replaces calls to cryptocomapere.get_historical_price function

    Names      | Date	    | timestamp  |Rate
    -----------|------------|----------- |-----------
    BTC -> ETH | 2017-12-11	| 1512950400 | 32.91
    BTC -> EUR | 2017-12-11	| 1512950400 | 13006.11
    BTC -> EUR | 2018-01-05	| 1514764800 | 12268.25
    XLM -> BTC | 2018-01-02	| 1509753600 | 0.00003136
    LTC -> EUR | 2017-11-07	| 1515110400 | 48.52
    BNB -> BTC | 2017-12-28	| 1514419200 | 0.0006253
    """

    if base == "BTC" and target == "ETH" and timestamp == 1512950400:
        return {"BTC": {"ETH": 32.91}}
    elif base == "BTC" and target == "EUR" and timestamp == 1512950400:
        return {"BTC": {"EUR": 13006.11}}
    elif base == "BTC" and target == "EUR" and timestamp == 1514764800:
        return {"BTC": {"EUR": 12268.25}}
    elif base == "XLM" and target == "BTC" and timestamp == 1509753600:
        return {"XLM": {"BTC": 0.00003136}}
    elif base == "LTC" and target == "EUR" and timestamp == 1515110400:
        return {"LTC": {"EUR": 48.52}}
    elif base == "BNB" and target == "BTC" and timestamp == 1514419200:
        return {"BNB": {"BTC": 0.0006253}}

    return {}  # fail since there is no data for this request


def test_name_converter(monkeypatch: MonkeyPatch):
    """
    Tests the conversion of one name to another at a specific date

    Amount	 | To  | Date	    | Result
    ---------|-----|------------|---------------
    5	 BTC | ETH | 2017-12-11 | 164.55   ETH
    1	 BTC | EUR | 2017-12-11 | 13006.11 EUR
    0.1	 BTC | EUR | 2018-01-05 | 1226.825 EUR
    1500 XLM | BTC | 2018-01-02 | 0.04704  BTC
    5	 LTC | EUR | 2017-11-07 | 242.6    EUR
    300	 BNB | BTC | 2017-12-28 | 0.18759  BTC
    """
    monkeypatch.setattr(cryptocompare, "get_historical_price",
                        new_get_historical_price)

    result = get_name_price(5, "BTC", "ETH", 1512950400)
    assert round(result, 2) == 164.55

    result = get_name_price(1, "BTC", "EUR", 1512950400)
    assert round(result, 2) == 13006.11

    result = get_name_price(0.1, "BTC", "EUR", 1514764800)
    assert round(result, 3) == 1226.825

    result = get_name_price(1500, "XLM", "BTC", 1509753600)
    assert round(result, 5) == 0.04704

    result = get_name_price(5, "LTC", "EUR", 1515110400)
    assert round(result, 1) == 242.6

    result = get_name_price(300, "BNB", "BTC", 1514419200)
    assert round(result, 6) == 0.18759