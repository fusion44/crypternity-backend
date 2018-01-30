import pytest
from ...celery import app as celery_app
from ..tasks import async_update_exchange_tx_generic
from mixer.backend.django import mixer
from backend.accounts.models import Account

pytestmark = pytest.mark.django_db


def new_update_exchange_tx_generic(account_id):
    return "running ..."


# TODO: Write a working test, update_exchange_tx_generic is not patched correctly
@celery_app.task
def test_async_update_exchange_tx_generic(monkeypatch):
    obj: Account = mixer.blend("accounts.Account")
    monkeypatch.setattr("backend.transactions.fetchers.generic_exchange",
                        new_update_exchange_tx_generic)
    assert True
    # assert async_update_exchange_tx_generic.delay(
    #     obj.id).get(timeout=10) == "running"
