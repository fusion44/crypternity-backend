import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

import backend.transactions.schema as schema
from backend.transactions.models import Transaction
from backend.test_utils.utils import mock_resolve_info

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


def test_import_csv_data_mutation(mocker):
    """
    test if user is authenticated ✓
    test fail at erroneous data input ✓
    test if appropriate import function is called ✓
    """
    usera = mixer.blend("auth.User")

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    mut = schema.ImportTransactionsMutation()
    res = mut.mutate(None, resolve_info, {})
    assert res.status == 403, "Should return 403 if user is not logged in"

    data = schema.ImportTransactionsMutation.Input()
    data.data = schema.ImportTransactionInput()
    data.data.service_type = "fakeexchange"
    data.data.import_mechanism = "csv"
    data.data.transactions = []

    req.user = usera
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 404, "Service not found, should return 404"
    assert res.formErrors == "Service type {} not found".format(
        data.data.service_type
    ), "Service not found, send correct error message"

    mocker.patch("backend.transactions.schema.import_data_livecoin")

    data.data.service_type = "livecoin"
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 200
    schema.import_data_livecoin.assert_called_once()  # pylint: disable=E1101
