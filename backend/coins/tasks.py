"""Contains all async tasks necessary for Accounts"""

from __future__ import absolute_import, unicode_literals
import cryptocompare

from backend.celery import app
from backend.coins.models import Coin


@app.task(bind=True)
def async_update_supported_coins(self):
    """Starts a celery async task to update supported coins"""
    self.update_state(state='RUNNING', meta={'current': 0, 'total': 100})
    coins_list = cryptocompare.get_coin_list(False)
    new_coins = 0
    updated = 0
    length = len(coins_list)

    print_counter = 0
    for idx, coin_key in enumerate(coins_list):
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

        percent_done = int((idx + 1) / length * 100)

        self.update_state(
            state='RUNNING', meta={
                'current': percent_done,
                'total': 100
            })

        print_counter += 1
        if print_counter is 30:
            print("Status: {}%".format(percent_done))
            print_counter = 0

    print("new: {} updated: {}".format(new_coins, updated))
    self.update_state(state='SUCCESS', meta={'current': 100, 'total': 100})
