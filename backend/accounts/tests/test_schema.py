import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

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


def test_create_account_mutation():
    user = mixer.blend("auth.User")
    mut = schema.CreateAccountMutation()

    data = {"name": "test1", "description": "desc1"}

    req = RequestFactory().get("/")
    # AnonymousUser() is equal to a not logged in user
    req.user = AnonymousUser()
    res = mut.mutate(None, req, data)
    assert res.status == 403, "Should return 403 if user is not logged in"

    req.user = user
    res = mut.mutate(None, req, {})
    assert res.status == 400, "Should return 400 if there are form errors"
    assert "account" in res.formErrors, "Should have form error for account in field"

    req.user = user
    res = mut.mutate(None, req, data)
    assert res.status == 200, 'Should return 200 if user is logged in and submits valid data'
    assert res.account.pk == 1, 'Should create new account'
