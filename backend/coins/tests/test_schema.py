'''Contains all schema tests for the application'''
import pytest
from mixer.backend.django import mixer
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from ...test_utils.utils import mock_resolve_info

from .. import schema

pytestmark = pytest.mark.django_db


def test_coin_type():
    instance = schema.CoinType()
    assert instance


def test_resolve_all_coins():
    '''Test allCoins Query'''
    user_a = mixer.blend('auth.User')

    req = RequestFactory().get('/')
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)

    mixer.blend('coins.Coin')
    mixer.blend('coins.Coin')
    mixer.blend('coins.Coin')
    mixer.blend('coins.Coin')

    query = schema.Query()
    res = query.resolve_all_coins(resolve_info)
    assert res.count() == 0, 'User not logged in, should return 0 transactions'

    req.user = user_a
    res = query.resolve_all_coins(resolve_info)
    assert res.count(
    ) == 4, 'User A is logged in, should return 4 transactions'
