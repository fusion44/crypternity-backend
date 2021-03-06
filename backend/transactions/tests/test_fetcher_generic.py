"""Contains all tests for the generic exchange fetcher"""
import time
from datetime import datetime, timedelta
import pytest
from django.utils.timezone import now
from _pytest.monkeypatch import MonkeyPatch
from mixer.backend.django import mixer
import ccxt
import cryptocompare

from backend.accounts.models import Account
from backend.transactions.models import Transaction
from backend.transactions.models import TransactionUpdateHistoryEntry

from ..fetchers.generic_exchange import update_exchange_trx_generic

pytestmark = pytest.mark.django_db


def new_get_historical_price(coin, curr="EUR", timestamp=time.time()):
    return {coin: {curr: 2000.0}}


def new_load_markets(self):
    return {
        'BTC/ETH': {},
    }


BINANCE_CHECK_TRANSACTION_ID = 2
BINANCE_AMOUNT = 0.20931215
BINANCE_COST = 0.00357691
BINANCE_PRICE = 0.01708888
BINANCE_BOOK_PRICE_EUR = \
        new_get_historical_price("BTC")["BTC"]["EUR"] * BINANCE_AMOUNT


def new_fetch_my_trades(self, symbol=None, since=None, limit=None, params={}):
    ret_binance = [{
        'amount': 0.1,
        'cost': 0.0003,
        'datetime': '2018-01-10T06:03:29.213Z',
        'fee': {
            'cost': 0.0002,
            'currency': 'BNB'
        },
        'id': '1',
        'price': 0.1,
        'side': 'sell',
        'symbol': 'BTC/ETH',
        'timestamp': 1515564209213,
    }, {
        'amount': BINANCE_AMOUNT,
        'cost': BINANCE_COST,
        'datetime': '2017-12-28T09:26:52.249Z',
        'fee': {
            'cost': 0.011,
            'currency': 'BNB'
        },
        'id': '2',
        'price': BINANCE_PRICE,
        'side': 'sell',
        'symbol': 'LTC/BTC',
        'timestamp': 1514453212249,
    }, {
        'amount': 240.0,
        'cost': 0.01,
        'datetime': '2018-01-08T18:23:09.665Z',
        'fee': {
            'cost': 0.0037,
            'currency': 'BNB'
        },
        'id': '3',
        'price': 4.335e-05,
        'side': 'buy',
        'symbol': 'XMR/BTC',
        'timestamp': 1515694988665,
    }]

    ret_cryptopia = [{
        'amount': 7.58039241,
        'cost': 0.00356278,
        'datetime': '2018-01-16T06:04:09.889Z',
        'fee': {
            'cost': 7.13e-06,
            'currency': 'BTC'
        },
        'id': '1',
        'price': 0.00047,
        'side': 'buy',
        'symbol': 'EMC/BTC',
        'timestamp': 1516082648889,
    }, {
        'amount': 0.20931215,
        'cost': 0.00357691,
        'datetime': '2018-01-16T05:59:03.521Z',
        'fee': {
            'cost': 7.15e-06,
            'currency': 'BTC'
        },
        'id': '2',
        'price': 0.01708888,
        'side': 'sell',
        'symbol': 'LTC/BTC',
        'timestamp': 1516082342521,
    }, {
        'amount': 130.77497801,
        'cost': 0.0353184,
        'datetime': '2017-12-25T20:25:33.460Z',
        'fee': {
            'cost': 7.064e-05,
            'currency': 'LTC'
        },
        'id': '3',
        'price': 0.00027007,
        'side': 'buy',
        'symbol': 'DGB/LTC',
        'timestamp': 1514233533460,
    }, {
        'amount': 130.77497801,
        'cost': 0.0353184,
        'datetime': '2017-12-25T20:25:33.460Z',
        'fee': {
            'cost': 7.064e-05,
            'currency': 'LTC'
        },
        'id': '4',
        'price': 0.00027007,
        'side': 'buy',
        'symbol': 'DGB/LTC',
        'timestamp': 1514233533460,
    }]

    if symbol is None:
        return ret_cryptopia
    else:
        return ret_binance


@pytest.fixture
def patch_ccxt(monkeypatch: MonkeyPatch):
    monkeypatch.setattr(ccxt.binance, "load_markets", new_load_markets)
    monkeypatch.setattr(ccxt.binance, "fetch_my_trades", new_fetch_my_trades)
    monkeypatch.setattr(ccxt.cryptopia, "load_markets", new_load_markets)
    monkeypatch.setattr(ccxt.cryptopia, "fetch_my_trades", new_fetch_my_trades)
    monkeypatch.setattr(cryptocompare, "get_historical_price",
                        new_get_historical_price)


def test_update_exchange_trx_generic_binance(monkeypatch: MonkeyPatch):
    user = mixer.blend("auth.User")
    account_bin: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="binance")
    account_crypt: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="cryptopia")

    patch_ccxt(monkeypatch)

    update_exchange_trx_generic(account_bin)
    update_exchange_trx_generic(account_crypt)

    t = Transaction.objects.filter(target_peer=account_bin)
    assert t.count() == 3

    t = Transaction.objects.filter(target_peer=account_crypt)
    assert t.count() == 4

    t: Transaction = Transaction.objects.get(pk=BINANCE_CHECK_TRANSACTION_ID)
    assert float(t.spent_amount) == BINANCE_AMOUNT
    assert float(t.acquired_amount) == BINANCE_COST
    assert float(t.book_price_eur) == BINANCE_BOOK_PRICE_EUR

    update_entry = TransactionUpdateHistoryEntry.objects.get(
        account=account_bin)
    assert update_entry.fetched_transactions == 3
    update_entry = TransactionUpdateHistoryEntry.objects.get(
        account=account_crypt)
    assert update_entry.fetched_transactions == 4


def test_update_exchange_trx_generic_transaction_history(
        monkeypatch: MonkeyPatch):
    """  Test, that the update function does not import  """
    user = mixer.blend("auth.User")
    account_bin: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="binance")

    patch_ccxt(monkeypatch)

    date: datetime = now()

    mixer.blend(
        "transactions.TransactionUpdateHistoryEntry",
        date=date,
        account=account_bin,
        fetched_transactions=3)

    monkeypatch.setattr(
        ccxt.binance, "fetch_my_trades",
        lambda self, symbol=None, since=None, limit=None, params={}:
        [
            {
                'amount': 0.3,
                'cost': 0.00032,
                'datetime': str(date + timedelta(days=-1)),  # Should be discarded
                'fee': {
                    'cost': 0.00044,
                    'currency': 'BNB'
                },
                'id': '4',
                'price': 0.1,
                'side': 'sell',
                'symbol': 'BTC/ETH',
                'timestamp': 1515564209213,
            },
            {
                'amount': BINANCE_AMOUNT,
                'cost': BINANCE_COST,
                'datetime': str(date + timedelta(days=1)),
                'fee': {
                    'cost': 0.011,
                    'currency': 'BNB'
                },
                'id': '5',
                'price': BINANCE_PRICE,
                'side': 'sell',
                'symbol': 'LTC/BTC',
                'timestamp': 1514453212249,
            }
        ])

    update_exchange_trx_generic(account_bin)
    transaction = Transaction.objects.filter(target_peer=account_bin)
    assert transaction.count(
    ) == 1, "Should not import transactions older than last update time"
