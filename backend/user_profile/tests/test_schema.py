import pytest
from mixer.backend.django import mixer
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from .. import schema

from ...test_utils.utils import mock_resolve_info

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_user_type():
    instance = schema.UserType()
    assert instance, "Should instanciate a UserType object"


def test_resolve_current_user():
    '''Test resolve_current_user Query'''
    query = schema.Query()
    req = RequestFactory().get("/")
    req.user = AnonymousUser()
    resolve_info = mock_resolve_info(req)
    res = query.resolve_get_current_user(resolve_info)
    assert res is None, "Should return None if user is not authenticated"

    user = mixer.blend("auth.User")
    req.user = user
    res = query.resolve_get_current_user(resolve_info)
    assert res == user, "Should return the current user if authenticated"
