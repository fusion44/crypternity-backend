from __future__ import absolute_import, unicode_literals
import time
import celery

from backend.celery import app
from backend.accounts.models import Account

from backend.transactions.fetchers.generic_exchange import update_exchange_tx_generic


@app.task(bind=True)
def async_update_exchange_tx_generic(self, account_id):
    print("Start task ", account_id)
    account = Account.objects.get(pk=account_id)
    self.update_state(state='RUNNING', meta={'current': 0, 'total': 3})
    update_exchange_tx_generic(account)
    self.update_state(state='SUCCESS', meta={'current': 3, 'total': 3})
