import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db

# Great introduction to TDD with Python + Django:
# https://www.youtube.com/watch?v=41ek3VNx_6Q


def test_project_creation():
    obj = mixer.blend("projects.Project")
    assert obj.pk > 0, "Should create a Project instance"


def test_project_str_func():
    name = "test123"
    obj = mixer.blend("projects.Project", name=name)
    assert obj.__str__() == name, "Should be the project's name"
