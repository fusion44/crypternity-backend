from graphql.execution.base import ResolveInfo


def mock_resolve_info(req) -> ResolveInfo:
    return ResolveInfo(None, None, None, None, None, None, None, None, None,
                       req)