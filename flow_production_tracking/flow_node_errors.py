"""Errors the Flow Production Tracking nodes raise beyond what `NodeError` builds itself.

A missing secret and a failed HTTP call come from `NodeError.from_missing_secret` and
`NodeError.from_request_exception`. Node files import this module by bare name, because the engine
loads each node file on its own with this folder on `sys.path`.
"""

import httpx
from griptape_nodes.exe_types.core_types import NodeError, NodeErrorLink

API_KEY_NAME = "SHOTGRID_API_KEY"
URL_NAME = "SHOTGRID_URL"
SCRIPT_NAME_NAME = "SHOTGRID_SCRIPT_NAME"
PROVIDER = "Autodesk Flow"
SCRIPT_DOCS_URL = "https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_py_python_api_create_manage_html"

HTTP_FORBIDDEN = 403


def parameter_label(parameter_name: str) -> str:
    """The parameter as the editor labels it, for example 'Project ID' for `project_id`."""
    return " ".join("ID" if word == "id" else word.capitalize() for word in parameter_name.split("_"))


def required_input_error(parameter_name: str, *, hint: str = "Enter a value.") -> NodeError:
    return NodeError(f"'{parameter_label(parameter_name)}' is required. {hint}", fields={"parameter": parameter_name})


def integer_input_error(parameter_name: str, value: object) -> NodeError:
    return NodeError(
        f"'{parameter_label(parameter_name)}' must be a whole number such as 123. It is set to {value!r}.",
        fields={"parameter": parameter_name},
    )


def missing_credential_errors(secrets: dict[str, str | None]) -> list[Exception]:
    """One error per unset secret in `secrets` (name to value)."""
    key_urls = {API_KEY_NAME: SCRIPT_DOCS_URL}
    return [
        NodeError.from_missing_secret(name, key_url=key_urls.get(name)) for name, value in secrets.items() if not value
    ]


def sign_in_error(exc: httpx.HTTPStatusError) -> NodeError:
    """Autodesk Flow refused the script name and API key when asked for an access token."""
    error = NodeError.from_http_response(exc.response, provider=PROVIDER, secret_name=API_KEY_NAME, key_refused=True)
    error.links.append(NodeErrorLink.from_secret(SCRIPT_NAME_NAME, "Update the script name"))
    return error


def to_node_error(exc: Exception) -> Exception:
    """A NodeError for an httpx failure, and any other exception unchanged."""
    if not isinstance(exc, httpx.HTTPError):
        return exc
    # A 403 means the script lacks a permission, not that the key was refused.
    response = getattr(exc, "response", None)
    key_refused = False if response is not None and response.status_code == HTTP_FORBIDDEN else None
    error = NodeError.from_request_exception(exc, provider=PROVIDER, secret_name=API_KEY_NAME, key_refused=key_refused)
    error.__cause__ = exc
    return error
