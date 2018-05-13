import pytest
import ccxt
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from ...test_utils.utils import mock_resolve_info

from backend.accounts.models import Account, CryptoAddress
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
    anonuser = AnonymousUser()
    usera = mixer.blend("auth.User")
    userb = mixer.blend("auth.User")

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    mixer.blend("accounts.Account", owner=usera)
    mixer.blend("accounts.Account", owner=usera)

    mixer.blend("accounts.Account", owner=userb)
    mixer.blend("accounts.Account", owner=userb)
    mixer.blend("accounts.Account", owner=userb)

    query = schema.Query()
    res = query.resolve_all_accounts(resolveInfo)
    assert res.count() == 0, "User not logged in, should return 0 accounts"

    req.user = usera
    res = query.resolve_all_accounts(resolveInfo)
    assert res.count() == 2, "User A is logged in, should return 2 accounts"

    req.user = userb
    res = query.resolve_all_accounts(resolveInfo)
    assert res.count() == 3, "User B is logged in, should return 3 accounts"


def test_resolve_get_crypto_addresses():
    # 1 Should not be able to anonymously get addresses
    # 2 Should not be able to get another users addresses
    # 3 Should return 0 if account does not exist
    # 4 Should return 0 if no peer id is passed in
    # 5 Should successfully receive addresses if conditions are met
    user_a = mixer.blend("auth.User")
    user_b = mixer.blend("auth.User")
    account_a: Account = mixer.blend("accounts.Account", owner=user_a)
    account_b: Account = mixer.blend("accounts.Account", owner=user_b)

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    mixer.blend("accounts.CryptoAddress", peer=account_a)
    mixer.blend("accounts.CryptoAddress", peer=account_a)
    mixer.blend("accounts.CryptoAddress", peer=account_a)

    mixer.blend("accounts.CryptoAddress", peer=account_b)
    mixer.blend("accounts.CryptoAddress", peer=account_b)
    mixer.blend("accounts.CryptoAddress", peer=account_b)

    query = schema.Query()
    res = query.resolve_get_crypto_addresses(resolve_info,
                                             **{"peer_id": account_a.id})
    assert res.count() == 0, "User not logged in, should return 0 addresses"

    req.user = user_b
    res = query.resolve_get_crypto_addresses(resolve_info,
                                             **{"peer_id": account_a.id})
    assert res.count() == 0, """
    User b requests addresses for account of user a, should return no addresses"""

    req.user = user_a
    res = query.resolve_get_crypto_addresses(resolve_info, **{"peer_id": 15})
    assert res.count(
    ) == 0, """Non existing peer, should return no addresses"""

    res = query.resolve_get_crypto_addresses(resolve_info, **{})
    assert res.count() == 0, "No peer ID passed, should return Error"

    res = query.resolve_get_crypto_addresses(resolve_info,
                                             **{"peer_id": account_a.id})
    assert res.count() == 3, "Valid request should return 3 addresses"


def test_resolve_supported_services():
    query = schema.Query()
    res = query.resolve_supported_services(None)
    assert len(res) > 0, "Should return more than one service"


def test_resolve_supported_symbols():
    query = schema.Query()

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    res = query.resolve_supported_symbols(resolveInfo,
                                          **{"service": "binance"})
    assert len(res) == 0, "User not logged in, should return 0 symbols"

    req.user = mixer.blend("auth.User")
    res = query.resolve_supported_symbols(resolveInfo,
                                          **{"service": "binance"})
    assert len(res) > 0, "User logged in, should return at least one symbol"


def test_create_account_mutation():
    mut = schema.CreateAccountMutation()

    data = {
        "name": "test1",
        "service_type": "binance",
        "symbols": '["ETH/BTC", "XLM/ETH"]',
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


def test_edit_account_mutation():
    # 1 Should not be able to to edit accounts when unauthenticated (status 403)
    # 2 Should not be able to edit other users accounts (status 403)
    # 3 Should return error message when no id or wrong data type was supplied (status 400)
    # 4 Should return success message when update was successfuly started (status 200)
    mut = schema.EditAccountMutation()

    anonuser = AnonymousUser()
    usera = mixer.blend("auth.User")
    userb = mixer.blend("auth.User")

    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)
    name_initial = "test1"
    name_updated = "test2"

    account: Account = mixer.blend(
        "accounts.Account",
        owner=usera,
        name=name_initial,
        service_type="binance",
        symbols='["ETH/BTC", "XLM/ETH"]',
        api_key="ateswg",
        api_secret="ssdge")

    data = {
        "account_id": account.pk,
        "name": name_updated,
        "api_key": "1234",
        "api_secret": "5678"
    }

    req = RequestFactory().get("/")
    # AnonymousUser() is equal to a not logged in user
    req.user = AnonymousUser()

    resolve_info = mock_resolve_info(req)

    res = mut.mutate(None, resolve_info, data)
    account: Account = Account.objects.get(pk=account.pk)
    assert account.name == name_initial, "Should not have edited name"
    assert res.status == 403, "Should return 403 if user is not logged in"

    req.user = userb
    res = mut.mutate(None, resolve_info, data)
    account: Account = Account.objects.get(pk=account.pk)
    assert account.name == name_initial, "Should not have edited name"
    assert res.status == 403, "Should return 403 if user is trying to modify another users account"

    req.user = usera
    res = mut.mutate(
        None, resolve_info, {
            "account_id": 5,
            "name": name_updated,
            "api_key": "1234",
            "api_secret": "5678"
        })
    assert res.status == 422, "Should return 422 if account does not exist"

    res = mut.mutate(None, resolve_info, {})
    account: Account = Account.objects.get(pk=account.pk)
    assert account.name == name_initial, "Should not have edited name"
    assert res.status == 400, "Should return 400 if there are form errors"
    assert "account" in res.formErrors, "Should have form error for account in field"

    res = mut.mutate(None, resolve_info, data)
    assert res.status == 200, 'Should return 200 if user is logged in and submits valid data'
    assert res.account.name == name_updated, 'Name should match'
    assert res.account.api_key == data["api_key"], 'API Key should match'
    assert res.account.api_secret == data[
        "api_secret"], 'API secret should match'


def test_create_crypto_address_mutation():
    # 1 Should not be able to to trigger mutation when unauthenticated (status 403)
    # 2 Should return error when account does not exist (status 404)
    # 3 Should return error when account does not belong to the logged in user (status 403)
    # 4 Should return error when coin does not exist (status 404)
    # 5 Should return success message and address info when address was successfully added (status 200)
    # 6 Default value for watch should be false

    user_a = mixer.blend("auth.User")
    user_b = mixer.blend("auth.User")

    account_a: Account = mixer.blend("accounts.Account", owner=user_a)
    mixer.blend("accounts.Account", owner=user_b)

    coin_a = mixer.blend("coins.Coin")

    mut = schema.CreateCryptoAddressMutation()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    data = {
        "account_id": 199,  # non existing account id
        "address": "addr_a",
        "coin_id": coin_a.id,
        "client_mutation_id": "test"
    }

    res = mut.mutate(None, resolve_info, data)
    assert res.status == 403, """
    Should not be able to to trigger mutation when unauthenticated"""
    assert res.client_mutation_id == "test"

    req.user = user_a
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 404, "Should return error when account does not exist"
    assert "account_id" in res.formErrors, """
    Should return an error message containing 'account_id'"""
    assert res.client_mutation_id == "test"

    # User B tries to add an address to User A's account
    req.user = user_b
    data["account_id"] = account_a.id
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 403, """
    Should return error when account does not belong to the logged in user"""
    assert res.client_mutation_id == "test"

    req.user = user_a
    data["coin_id"] = 199
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 404, "Should return error when coin does not exist"
    assert "coin_id" in res.formErrors, """
    Should return an error message containing 'account_id'"""
    assert res.client_mutation_id == "test"

    data["coin_id"] = coin_a.id
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 200, "Should return success message when update was successfully started"
    assert res.address is not None, "Address must not be None"
    assert res.client_mutation_id == "test"
    assert not res.address.watch, "Default watch should be False"

    data["watch"] = True
    res = mut.mutate(None, resolve_info, data)
    assert res.address.watch, "Watch should be True"


def test_edit_crypto_address_mutation():
    # 1 Should not be able to to trigger mutation when unauthenticated (status 403)
    # 2 Should return error when address does not exist (status 404)
    # 3 Should return error when address does not belong to the logged in user (status 403)
    # 4 Should return error when coin does not exist (status 404)
    # 5 Should return success message and address info when address was
    #   successfully edited (status 200)
    # 6 Default value for watch should be false

    user_a = mixer.blend("auth.User")
    user_b = mixer.blend("auth.User")

    account_a: Account = mixer.blend("accounts.Account", owner=user_a)
    mixer.blend("accounts.Account", owner=user_b)

    coin_a = mixer.blend("coins.Coin")
    coin_b = mixer.blend("coins.Coin")

    crypto_address_a: CryptoAddress = mixer.blend(
        "accounts.CryptoAddress", peer=account_a, coin_id=coin_b.id)

    mut = schema.EditCryptoAddressMutation()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    data = {
        "id": 199,  # non existing address
        "address": "changed_addr",
        "coin_id": coin_a.id,
        "client_mutation_id": "test",
        "watch": True
    }

    res = mut.mutate(None, resolve_info, data)
    assert res.status == 403, """
    Should not be able to to trigger mutation when unauthenticated"""
    assert res.client_mutation_id == "test"

    req.user = user_a
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 404, "Should return error when address object does not exist"
    assert "id" in res.formErrors, """
    Should return an error message containing 'id'"""
    assert res.client_mutation_id == "test"

    # User B tries to edit an address of User A
    req.user = user_b
    data["id"] = crypto_address_a.id
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 403, """
    Should return error when address does not belong to the logged in user"""
    assert res.client_mutation_id == "test"

    req.user = user_a
    data["coin_id"] = 199
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 404, "Should return error when coin does not exist"
    assert "coin_id" in res.formErrors, """
    Should return an error message containing 'account_id'"""
    assert res.client_mutation_id == "test"

    data["coin_id"] = coin_a.id
    res = mut.mutate(None, resolve_info, data)
    assert res.status == 200, "Should return success message when update was successfully started"
    assert res.address.address == "changed_addr", "Address must be 'changed_addr'"
    assert res.client_mutation_id == "test"
    assert res.address.coin.id == coin_a.id, "Coin should be Coin A now"
    assert res.address.watch, "Watch should be True"


def test_refresh_transactions_mutation(monkeypatch):
    # 1 Should not be able to to trigger mutation when unauthenticated (status 403)
    # 2 Should not be able to update other users accounts (status 403)
    # 3 Should return error message when no id or wrong data type was supplied (status 400)
    # 4 Should return success message when update was successfuly started (status 200)

    usera = mixer.blend("auth.User")
    userb = mixer.blend("auth.User")

    mixer.blend("accounts.Account", owner=usera)  # id 1
    mixer.blend("accounts.Account", owner=userb)  # id 2

    mut = schema.AccountRefreshTransactionsMutation()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolveInfo = mock_resolve_info(req)

    data = {"account_id": "1"}
    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 403, 'Should not be able to to trigger mutation when unauthenticated (status 403)'

    req.user = userb
    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 403, 'Should not be able to update other users accounts (status 403)'

    res = mut.mutate(None, resolveInfo, {})
    assert res.status == 400, 'Should return error status when supplied no input at all'

    data = {"account_id": "a"}
    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 400, 'Should return error status when supplied incorrect input'

    data = {"account_id": "-1"}
    res = mut.mutate(None, resolveInfo, data)
    assert res.status == 400, 'Should return error status when supplied incorrect input'

    # TODO: Find reason why this won't work
    #
    ## This prints True:
    # print(
    #     hasattr(backend.transactions.fetchers.generic_exchange,
    #             "update_exchange_trx_generic"))
    #
    ## but the Lambda is never used
    #monkeypatch.setattr(backend.transactions.fetchers.generic_exchange,
    #                    "update_exchange_trx_generic",
    #                    new_update_exchange_trx_generic)
    #req.user = usera
    #res = mut.mutate(None, resolveInfo, data)
    #assert res.status == 200, 'Should return success message when update was successfuly started (status 200)'
