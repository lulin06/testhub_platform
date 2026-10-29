"""Helpers for OpenAPI-style single-brace path parameters."""

import re
from urllib.parse import quote


PATH_PARAMETER_RE = re.compile(r'(?<!\{)\{([^{}]+)\}(?!\})')


def resolve_path_parameters(url, params):
    """Substitute `{name}` path values and return remaining query parameters."""
    if not isinstance(params, dict):
        return url, params or {}

    query_params = params.copy()

    def substitute(match):
        key = match.group(1).strip()
        if key not in params:
            return match.group(0)
        value = params[key]
        query_params.pop(key, None)
        if value is None or value == '':
            return match.group(0)
        return quote(str(value), safe='')

    return PATH_PARAMETER_RE.sub(substitute, url or ''), query_params
