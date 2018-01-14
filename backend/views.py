from graphene_django.views import GraphQLView


# https://github.com/graphql-python/graphene-django/issues/252
class GraphQLErrorFormatView(GraphQLView):
    @staticmethod
    def format_error(error):
        print(error)
        if hasattr(error, 'original_error') and error.original_error:
            formatted = {"message": str(error.original_error)}
            if isinstance(error.original_error, UnauthorizedError):
                formatted['code'] = "401"
            elif isinstance(error.original_error, PermissionDeniedError):
                formatted['code'] = "403"
            return formatted

        return GraphQLView.format_error(error)
