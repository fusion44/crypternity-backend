'''Contains all task tests for this application'''
import pytest
from django.db.models.query import QuerySet
from backend.coins.models import Coin
from ...celery import app as celery_app
from ..tasks import async_update_supported_coins

pytestmark = pytest.mark.django_db


def new_get_coin_list(format_list):  #pylint: disable=W0613
    '''
    Fake cryptocompare.get_coin_list function
    Provides two valid and one invalid coins
    '''
    return {
        'BTC': {
            'Id': '1000',
            'ImageUrl': '/media/124/btc.png',
            'Name': 'Bitcoin',
            'Symbol': 'BTC',
            'CoinName': 'Bitcoin',
            'FullName': 'Bitcoin (BTC)'
        },
        'LTC': {
            'Id': '1001',
            'ImageUrl': '/media/124/ltc.png',
            'Name': 'Litecoin',
            'Symbol': 'LTC',
            'CoinName': 'Litecoin',
            'FullName': 'Litecoin (LTC)'
        },
        'BTCC': {
            # Should trigger an exception (Id not an int) and not be imported
            'Id': 'Except',
            'ImageUrl': '/media/124/btc.png',
            'Name': 'BitcoinCrash',
            'Symbol': 'BTCC',
            'CoinName': 'Bitcoin Crash',
            'FullName': 'Bitcoin Crash (BTCC)'
        }
    }


def new_get_coin_list_updated(format_list):  #pylint: disable=W0613
    '''
    Fake cryptocompare.get_coin_list function
    Provides one updated and one additional coin
    '''
    return {
        'LTC': {
            'Id': '1001',
            'ImageUrl': '/media/345/ltc_updated.png',
            'Name': 'Litecoin',
            'Symbol': 'LTC',
            'CoinName': 'Litecoin Updated',
            'FullName': 'Litecoin (LTC)'
        },
        'XLM': {
            'Id': '1002',
            'ImageUrl': '/media/1234/xlm.png',
            'Name': 'Stellar Lumens',
            'Symbol': 'XLM',
            'CoinName': 'Lumens',
            'FullName': 'Stellar Lumens (XLM)'
        }
    }


@celery_app.task
def test_async_update_coins(monkeypatch):
    '''Test the supported coin update function'''

    # Test import the objects
    monkeypatch.setattr('cryptocompare.get_coin_list', new_get_coin_list)
    async_update_supported_coins()
    all_coins: QuerySet = Coin.objects.all()
    assert all_coins.count() == 2

    coin: Coin = all_coins.first()
    assert coin.cc_id == 1000
    assert coin.img_url == '/media/124/btc.png'
    assert coin.name == 'Bitcoin'
    assert coin.symbol == 'BTC'
    assert coin.coin_name == 'Bitcoin'
    assert coin.full_name == 'Bitcoin (BTC)'

    # Test update the database object
    monkeypatch.setattr('cryptocompare.get_coin_list',
                        new_get_coin_list_updated)
    async_update_supported_coins()  # pylint: disable=E1120
    assert Coin.objects.all().count() == 3, 'Test add one new coin'
    ltc_updated: Coin = Coin.objects.get(pk=2)
    assert ltc_updated.cc_id == 1001
    assert ltc_updated.img_url == '/media/345/ltc_updated.png'
    assert ltc_updated.coin_name == 'Litecoin Updated'
