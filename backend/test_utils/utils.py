from graphql.execution.base import ResolveInfo


def mock_resolve_info(req):
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)