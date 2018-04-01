from datetime import datetime, timedelta
import json
import pytest
from django.utils.timezone import now
from _pytest.monkeypatch import MonkeyPatch
from mixer.backend.django import mixer
import coinbase
import cryptocompare

from backend.accounts.models import Account
from backend.transactions.models import Transaction

from ..fetchers.coinbase import update_coinbase_trx

pytestmark = pytest.mark.django_db


class MockAPIObject(dict):
    """Mock of coinbase APIObject"""

    def __init__(self, pagination=None, data=None):
        self.__pagination = pagination or {"next_uri": None}
        self["data"] = data or []
        super(MockAPIObject, self).__init__()

    @property
    def pagination(self):
        """Return the pagination data"""
        return self.__pagination


def new_get_accounts(self):
    """Fake coinbase get accounts for user"""
    return MockAPIObject(data=[{
        "id": "fiat_id",
        "type": "fiat"
    }, 
    {
        "id": "wallet_id_btc",
        "type": "wallet"
    }, 
    {
        "id": "wallet_id_ltc",
        "type": "wallet"
    }])


def new_get_buys(self, cb_account_id):
    """Fake get buys for account"""
    if cb_account_id == "wallet_id_btc":
        return MockAPIObject(data=[
            {
                "created_at": "2017-12-27T15:16:22Z",
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 0.04,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 300,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 4.4,
                        "currency": "EUR"
                    }
                }]
            },
            {
                "created_at": "2017-12-27T15:16:22Z",
                "resource": "buy",
                # should be skipped since it was canceled
                "status": "canceled"
            },
            {
                "created_at": "2018-01-28T13:11:35Z",
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 0.05,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 350,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 4.50,
                        "currency": "EUR"
                    }
                }]
            },
            {
                "created_at": "2018-01-28T13:11:35Z",
                # should be skipped and not end up in the database (neither sell nor buy)
                # and it's status is canceled
                "resource": "should be skipped",
                "status": "canceled",
                "amount": {
                    "amount": 0.05,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 350,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 4.50,
                        "currency": "EUR"
                    }
                }]
            }
        ])
    elif cb_account_id == "wallet_id_ltc":
        return MockAPIObject(
            data=[{
                "created_at": "2018-01-22T12:26:35Z",
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 2.2,
                    "currency": "LTC"
                },
                "total": {
                    "amount": 260,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 5,
                        "currency": "EUR"
                    }
                }]
            }, {
                "created_at": "2018-01-22T11:04:01Z",
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 1.4,
                    "currency": "LTC"
                },
                "total": {
                    "amount": 100,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 3,
                        "currency": "EUR"
                    }
                }]
            }])
    else:
        return MockAPIObject()


def new_get_sells(self, cb_account_id):
    """Fake get sells for account"""
    if cb_account_id == "wallet_id_btc":
        return MockAPIObject(
            data=[{
                "created_at": "2018-01-25T11:24:52Z",
                "resource": "sell",
                "status": "completed",
                "amount": {
                    "amount": 0.06,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 800,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 7,
                        "currency": "EUR"
                    }
                }]
            }])
    elif cb_account_id == "wallet_id_ltc":
        return MockAPIObject(
            data=[{
                "created_at": "2018-01-23T07:23:54Z",
                "resource": "sell",
                "status": "completed",
                "amount": {
                    "amount": 0.3,
                    "currency": "LTC"
                },
                "total": {
                    "amount": 80,
                    "currency": "EUR"
                },
                "fees": [{
                    "amount": {
                        "amount": 2,
                        "currency": "EUR"
                    }
                }]
            }])
    else:
        return MockAPIObject()


def new_get_transactions(self, cb_account_id):
    """Fake get transactions for account"""
    if cb_account_id == "wallet_id_ltc":
        return MockAPIObject(data=[{
            "id": "12234-6666-8888-0000-1111111111",
            "type": "send",
            "status": "completed",
            "amount": {
                "amount": "-0.2",
                "currency": "LTC"
            },
            "native_amount": {
                "amount": "-46.00",
                "currency": "EUR"
            },
            "description": None,
            "created_at": "2017-12-15T15:00:00Z",
            "updated_at": "2017-12-15T15:00:00Z",
            "resource": "transaction",
            "network": {
                "status": "confirmed",
                "hash": "123456789",
                "transaction_fee": {
                    "amount": "0.001",
                    "currency": "LTC"
                },
                "transaction_amount": {
                    "amount": "0.199",
                    "currency": "LTC"
                },
                "confirmations": 54000
            },
            "to": {
                "resource": "litecoin_address",
                "address": "LcnAddress1",
                "currency": "LTC"
            },
            "details": {
                "title": "Sent Litecoin",
                "subtitle": "To Litecoin address"
            }
        }, 
        {
            "id": "aaaaaaaaa-aaaa-aaaaaa-eeee-aaaaaa",
            "type": "send",
            "status": "completed",
            "amount": {
                "amount": "-0.4",
                "currency": "LTC"
            },
            "native_amount": {
                "amount": "-90.00",
                "currency": "EUR"
            },
            "description": None,
            "created_at": "2017-12-11T19:00:00Z",
            "updated_at": "2017-12-11T19:00:00Z",
            "resource": "transaction",
            "instant_exchange": False,
            "network": {
                "status": "confirmed",
                "hash": "123456789",
                "transaction_fee": {
                    "amount": "0.001",
                    "currency": "LTC"
                },
                "transaction_amount": {
                    "amount": "0.399",
                    "currency": "LTC"
                },
                "confirmations": 15387
            },
            "to": {
                "resource": "litecoin_address",
                "address": "LcnAddress2",
                "currency": "LTC"
            },
            "details": {
                "title": "Sent Litecoin",
                "subtitle": "To Litecoin address"
            }
        }, 
        {
            "id": "aaaaaaaaa-aaaa-aaaaaa-eeee-aaaaaa",
            "type": "send",
            "status": "completed",
            "amount": {
                "amount": "1.0",
                "currency": "LTC"
            },
            "native_amount": {
                "amount": "90.00",
                "currency": "EUR"
            },
            "description": None,
            "created_at": "2017-12-11T19:00:00Z",
            "updated_at": "2017-12-11T19:00:00Z",
            "resource": "transaction",
            "instant_exchange": False,
            "network": {
                "status": "off_blockchain",
            },
        }])
    else:
        return MockAPIObject()


def new_get_historical_price(base, target, date):
    """Fake crypto compare API"""
    if base == "BTC" and target == "EUR":
        return {"BTC": {"EUR": 10000}}
    elif base == "EUR" and target == "BTC":
        return {"EUR": {"BTC": 0.00012}}
    elif base == "LTC" and target == "BTC":
        return {"LTC": {"BTC": 0.02}}
    elif base == "LTC" and target == "EUR":
        return {"LTC": {"EUR": 250}}


def test_refresh_coinbase_trx(monkeypatch: MonkeyPatch):
    """Test import coinbase transactions"""
    user = mixer.blend("auth.User")
    account: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="coinbase")

    monkeypatch.setattr(cryptocompare, "get_historical_price",
                        new_get_historical_price)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_accounts",
                        new_get_accounts)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_transactions",
                        new_get_transactions)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_buys",
                        new_get_buys)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_sells",
                        new_get_sells)

    update_coinbase_trx(account)
    transaction = Transaction.objects.filter(target_peer=account)
    assert transaction.count() == 9, "Should import nine transations"


def new_get_buys_transaction_history(self, cb_account):
    """Fake coinbase get buys transation history"""
    date: datetime = now()
    if cb_account == "wallet_id_btc":
        return MockAPIObject(
            data=[{
                "created_at": str(date + timedelta(days=-1)),
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 10,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 10,
                    "currency": "BTC"
                },
                "fees": [{
                    "amount": {
                        "amount": 1,
                        "currency": "EUR"
                    }
                }]
            }, {
                "created_at": str(date + timedelta(days=1)),
                "resource": "buy",
                "status": "completed",
                "amount": {
                    "amount": 5,
                    "currency": "BTC"
                },
                "total": {
                    "amount": 5,
                    "currency": "BTC"
                },
                "fees": [{
                    "amount": {
                        "amount": 0.5,
                        "currency": "EUR"
                    }
                }]
            }])
    else:
        return MockAPIObject()


def test_update_trx_coinbase_transaction_history(monkeypatch: MonkeyPatch):
    """  Test, that the update function does not import  """
    user = mixer.blend("auth.User")
    account: Account = mixer.blend(
        "accounts.Account", owner=user, service_type="coinbase")

    date: datetime = now()

    monkeypatch.setattr(cryptocompare, "get_historical_price",
                        new_get_historical_price)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_accounts",
                        new_get_accounts)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_transactions",
                        new_get_transactions)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_buys",
                        new_get_buys_transaction_history)
    monkeypatch.setattr(coinbase.wallet.client.Client, "get_sells",
                        lambda self, cb_account: MockAPIObject())

    mixer.blend(
        "transactions.TransactionUpdateHistoryEntry",
        date=date,
        account=account,
        fetched_transactions=3)

    update_coinbase_trx(account)
    transaction = Transaction.objects.filter(target_peer=account)
    assert transaction.count(
    ) == 1, "Should not import transactions older than last update time"
