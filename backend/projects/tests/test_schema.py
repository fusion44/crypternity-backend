import pytest
from mixer.backend.django import mixer
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from .. import schema

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_project_type():
    instance = schema.ProjectType()
    assert instance


def test_resolve_get_project_by_id():
    mixer.blend("projects.Project")
    mixer.blend("projects.Project")
    mixer.blend("projects.Project")
    query = schema.Query()
    res = query.resolve_get_project(None, **{"id": 1})
    assert res.id == 1, "Should return project with id 1"

    res = query.resolve_get_project(None, **{"id": 2})
    assert res.id == 2, "Should return project with id 2"

    with pytest.raises(ObjectDoesNotExist) as excinfo:
        res = query.resolve_get_project(None, **{"id": 5})


def test_resolve_get_project_by_name():
    mixer.blend("projects.Project", name="first")
    mixer.blend("projects.Project", name="second")
    mixer.blend("projects.Project", name="third")

    query = schema.Query()
    res = query.resolve_get_project(None, **{"name": "first"})
    assert res.name == "first", "Should return project with name \"first\""

    res = query.resolve_get_project(None, **{"name": "third"})
    assert res.name == "third", "Should return project with name \"third\""

    with pytest.raises(ObjectDoesNotExist) as excinfo:
        res = query.resolve_get_project(None, **{"name": "nonexistend"})


def test_resolve_all_projects():
    mixer.blend("projects.Project")
    mixer.blend("projects.Project")
    query = schema.Query()
    res = query.resolve_all_projects(None)
    assert res.count() == 2, "Should return all projects"


def test_create_project_mutation():
    user = mixer.blend("auth.User")
    mut = schema.CreateProjectMutation()

    data = {"name": "test1", "description": "desc1"}

    req = RequestFactory().get("/")
    # AnonymousUser() is equal to a not logged in user
    req.user = AnonymousUser()
    res = mut.mutate(None, req, data)
    assert res.status == 403, "Should return 403 if user is not logged in"

    req.user = user
    res = mut.mutate(None, req, {})
    assert res.status == 400, "Should return 400 if there are form errors"
    assert "project" in res.formErrors, "Should have form error for project in field"

    req.user = user
    res = mut.mutate(None, req, data)
    assert res.status == 200, 'Should return 200 if user is logged in and submits valid data'
    assert res.project.pk == 1, 'Should create new project'
