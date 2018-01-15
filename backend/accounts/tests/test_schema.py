import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from ...test_utils.utils import mock_resolve_info

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_account_type():
    instance = schema.AccountType()
    assert instance


def test_resolve_get_accounts_by_id():
    mixer.blend("accounts.Account")
    mixer.blend("accounts.Account")
    mixer.blend("accounts.Account")
    query = schema.Query()
    res = query.resolve_get_account(None, **{"id": 1})
    assert res.id == 1, "Should return account with id 1"

    res = query.resolve_get_account(None, **{"id": 2})
    assert res.id == 2, "Should return account with id 2"

    with pytest.raises(ObjectDoesNotExist) as excinfo:
        res = query.resolve_get_account(None, **{"id": 5})


def test_resolve_get_account_by_name():
    mixer.blend("accounts.Account", name="first")
    mixer.blend("accounts.Account", name="second")
    mixer.blend("accounts.Account", name="third")

    query = schema.Query()
    res = query.resolve_get_account(None, **{"name": "first"})
    assert res.name == "first", "Should return account with name \"first\""

    res = query.resolve_get_account(None, **{"name": "third"})
    assert res.name == "third", "Should return account with name \"third\""

    with pytest.raises(ObjectDoesNotExist) as excinfo:
        res = query.resolve_get_account(None, **{"name": "nonexistend"})


def test_resolve_all_accounts():
    mixer.blend("accounts.Account")
    mixer.blend("accounts.Account")
    query = schema.Query()
    res = query.resolve_all_accounts(None)
    assert res.count() == 2, "Should return all accounts"


def test_resolve_supported_services():
    query = schema.Query()
    res = query.resolve_supported_services(None)
    assert len(res) > 0, "Should return more than one service"


def test_create_account_mutation():
    mut = schema.CreateAccountMutation()

    data = {
        "name": "test1",
        "service_type": "binance",
        "api_key": "ateswg",
        "api_secret": "ssdge"
    }

    req = RequestFactory().get("/")
    # AnonymousUser() is equal to a not logged in user
    req.user = AnonymousUser()

    resolveInfo = mock_resolve_info(req)

    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 403, "Should return 403 if user is not logged in"

    req.user = mixer.blend("auth.User")
    res = mut.mutate(None, resolveInfo, {})
    assert res.status == 400, "Should return 400 if there are form errors"
    assert "account" in res.formErrors, "Should have form error for account in field"

    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 200, 'Should return 200 if user is logged in and submits valid data'
    assert res.account.pk == 1, 'Should create new account'

    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 422, 'Should return 422 if account with this name exists'
