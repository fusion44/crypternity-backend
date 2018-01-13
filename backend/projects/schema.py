import json
import graphene

from graphene_django.types import DjangoObjectType

from backend.projects.models import Project


class ProjectType(DjangoObjectType):
    class Meta:
        model = Project


class Query(object):
    # Single project by ID or name
    get_project = graphene.Field(
        ProjectType,
        id=graphene.Int(required=False),
        name=graphene.String(required=False))

    def resolve_get_project(self, info, **kwargs):
        project_id = kwargs.get('id')
        project_name = kwargs.get('name')

        if project_id is not None:
            return Project.objects.get(pk=project_id)
        if project_name is not None:
            return Project.objects.get(name=project_name)

    # Get all projects where user has access rights
    all_projects = graphene.List(ProjectType)

    def resolve_all_projects(self, info, **kwargs):
        return Project.objects.all()


class CreateProjectMutation(graphene.relay.ClientIDMutation):
    class Input:
        name = graphene.String()
        description = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    project = graphene.Field(ProjectType)

    @classmethod
    def mutate(cls, root, info, input: Input):
        if not info.user.is_authenticated:
            return CreateProjectMutation(status=403)
        name = input.get("name", "").strip()
        description = input.get("description", "").strip()

        # TODO: validate input using django forms or whatnot
        if not name or not description:
            return CreateProjectMutation(
                status=400,
                formErrors=json.dumps({
                    "project": ["Please enter valid project data"]
                }))
        obj = Project.objects.create(
            creator=info.user, name=name, description=description)
        return CreateProjectMutation(status=200, project=obj)
