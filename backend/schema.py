import graphene

import backend.projects.schema
import backend.user_profile.schema


class Query(backend.user_profile.schema.Query, backend.projects.schema.Query,
            graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class Mutation(graphene.ObjectType):
    create_project = backend.projects.schema.CreateProjectMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)