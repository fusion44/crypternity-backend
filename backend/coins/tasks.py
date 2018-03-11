"""Contains all async tasks necessary for Accounts"""

from __future__ import absolute_import, unicode_literals
import cryptocompare

from backend.celery import app
from backend.coins.models import Coin


@app.task()
def async_update_supported_coins():
    """Starts a celery async task to update supported coins"""
    coins_list = cryptocompare.get_coin_list(False)
    new_coins = 0
    updated = 0
    for coin_key in coins_list:
        item = coins_list.get(coin_key)

        try:
            _id = int(item.get("Id"))
        except ValueError:
            continue

        try:
            coin: Coin = Coin.objects.get(cc_id=_id)
            updated += 1
        except Coin.DoesNotExist:
            coin = Coin()
            coin.cc_id = _id
            new_coins += 1

        coin.img_url = item.get('ImageUrl', '')
        coin.name = item.get('Name', '')
        coin.symbol = item.get('Symbol', '')
        coin.coin_name = item.get('CoinName', '')
        coin.full_name = item.get('FullName', '')
        coin.save()

    print("new: {} updated: {}".format(new_coins, updated))
