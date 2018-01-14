import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db

# Great introduction to TDD with Python + Django:
# https://www.youtube.com/watch?v=41ek3VNx_6Q


def test_account_creation():
    obj = mixer.blend("accounts.Account")
    assert obj.pk > 0, "Should create an Account instance"


def test_account_str_func():
    name = "test123"
    obj = mixer.blend("accounts.Account", name=name)
    assert obj.__str__() == name, "Should be the accounts's name"
