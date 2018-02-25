"""Contains all async tasks necessary for Accounts"""

from __future__ import absolute_import, unicode_literals

from backend.celery import app
from backend.accounts.models import Account

from backend.transactions.fetchers.generic_exchange import update_exchange_trx_generic
from backend.transactions.fetchers.coinbase import update_coinbase_trx


@app.task(bind=True)
def async_update_account_trx(self, account_id):
    """Starts a celery async task to update transaction for an account"""

    account: Account = Account.objects.get(pk=account_id)
    print("Starting task update transactions for account: ", account.name)

    self.update_state(state='RUNNING', meta={'current': 0, 'total': 3})
    if account.service_type == "coinbase":
        update_coinbase_trx(account)
    else:
        update_exchange_trx_generic(account)
    self.update_state(state='SUCCESS', meta={'current': 3, 'total': 3})
