import pytest
import ccxt
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from ...test_utils.utils import mock_resolve_info

from backend.transactions.models import Transaction
from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_transaction_type():
    instance = schema.TransactionType()
    assert instance


def test_resolve_get_transaction_by_id():
    anonuser = AnonymousUser()
    usera = mixer.blend("auth.User")
    userb = mixer.blend("auth.User")

    mixer.blend("transactions.Transaction", owner=usera)
    mixer.blend("transactions.Transaction", owner=usera)
    mixer.blend("transactions.Transaction", owner=usera)

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    query = schema.Query()
    res = query.resolve_get_transaction(resolveInfo, **{"id": 1})
    assert res == None, "User not logged in, should return None"

    query = schema.Query()
    req.user = usera
    res = query.resolve_get_transaction(resolveInfo, **{"id": 1})
    assert isinstance(res, Transaction), "Should return a transaction object"
    assert res.id == 1, "Should return transaction with id 1"

    res = query.resolve_get_transaction(resolveInfo, **{"id": 2})
    assert isinstance(res, Transaction), "Should return a transaction object"
    assert res.id == 2, "Should return transaction with id 2"

    req.user = userb
    res = query.resolve_get_transaction(resolveInfo, **{"id": 2})
    assert res == None, "User should not have access to another users transaction"

    with pytest.raises(ObjectDoesNotExist) as excinfo:
        res = query.resolve_get_transaction(resolveInfo, **{"id": 5})


def test_resolve_all_transactions():
    anonuser = AnonymousUser()
    usera = mixer.blend("auth.User")
    userb = mixer.blend("auth.User")

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    mixer.blend("transactions.Transaction", owner=usera)
    mixer.blend("transactions.Transaction", owner=usera)

    mixer.blend("transactions.Transaction", owner=userb)
    mixer.blend("transactions.Transaction", owner=userb)
    mixer.blend("transactions.Transaction", owner=userb)

    query = schema.Query()
    res = query.resolve_all_transactions(resolveInfo)
    assert res.count() == 0, "User not logged in, should return 0 transactions"

    req.user = usera
    res = query.resolve_all_transactions(resolveInfo)
    assert res.count(
    ) == 2, "User A is logged in, should return 2 transactions"

    req.user = userb
    res = query.resolve_all_transactions(resolveInfo)
    assert res.count(
    ) == 3, "User B is logged in, should return 3 transactions"
