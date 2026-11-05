"""Turns Flow Production Tracking failures into NodeError.

Node files import this module by bare name (`from flow_node_errors import ...`) because the engine loads
each node file on its own, with this folder on `sys.path` and no parent package.
"""

from typing import Any

import httpx
from griptape_nodes.exe_types.core_types import NodeError, NodeErrorLink

API_KEY_NAME = "SHOTGRID_API_KEY"
URL_NAME = "SHOTGRID_URL"
SCRIPT_NAME_NAME = "SHOTGRID_SCRIPT_NAME"

SCRIPT_DOCS_URL = "https://help.autodesk.com/view/SGDEV/ENU/?guid=SGD_py_python_api_create_manage_html"
REST_API_DOCS_URL = "https://developer.shotgridsoftware.com/rest-api/"

HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429
HTTP_SERVER_ERROR = 500


def settings_link(label: str, secret_name: str) -> NodeErrorLink:
    return NodeErrorLink(label=label, url=f"#settings-secrets?filter={secret_name}")


def parameter_label(parameter_name: str) -> str:
    """Return the name of a parameter as the editor shows it, for example 'Project ID' for `project_id`."""
    words = [("ID" if word == "id" else word.capitalize()) for word in parameter_name.split("_")]
    return " ".join(words)


def missing_api_key_error() -> NodeError:
    return NodeError(
        f"{API_KEY_NAME} is not set. Add it in Settings → API Keys & Secrets, then run the node again.",
        links=[
            settings_link("Add the API key", API_KEY_NAME),
            NodeErrorLink(label="Create a script key", url=SCRIPT_DOCS_URL),
        ],
    )


def missing_url_error() -> NodeError:
    return NodeError(
        f"{URL_NAME} is not set. Add your Autodesk Flow site URL (for example "
        "https://your-company.shotgrid.autodesk.com/) in Settings → API Keys & Secrets, "
        "then run the node again.",
        links=[settings_link("Add the Autodesk Flow URL", URL_NAME)],
    )


def required_input_error(parameter_name: str, *, hint: str = "") -> NodeError:
    """A required input is empty. `hint` says what to put there."""
    label = parameter_label(parameter_name)
    message = f"'{label}' is required. {hint}".strip() if hint else f"'{label}' is required. Enter a value."
    return NodeError(message, fields={"parameter": parameter_name})


def integer_input_error(parameter_name: str, value: Any) -> NodeError:
    label = parameter_label(parameter_name)
    return NodeError(
        f"'{label}' must be a whole number such as 123. It is set to {str(value)!r}.",
        fields={"parameter": parameter_name},
    )


def _first_api_error(body: Any) -> dict[str, Any]:
    """Return the first entry of the REST API's `errors` list, or an empty dict."""
    if isinstance(body, dict):
        errors = body.get("errors")
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            return errors[0]
    return {}


def _response_body(response: httpx.Response) -> dict[str, Any] | None:
    try:
        body = response.json()
    except ValueError:
        text = response.text.strip()
        return {"body": text[:2000]} if text else None
    return body if isinstance(body, dict) else {"body": body}


def _reason(api_error: dict[str, Any]) -> str:
    """The server's own explanation, preferring `detail` over the shorter `title`."""
    for key in ("detail", "title"):
        value = api_error.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().rstrip(".")
    return ""


def error_from_http_status(exc: httpx.HTTPStatusError) -> NodeError:
    response = exc.response
    status = response.status_code
    body = _response_body(response)
    api_error = _first_api_error(body)
    reason = _reason(api_error)

    fields: dict[str, str | int | float | bool] = {"status_code": status}
    code = api_error.get("code")
    if isinstance(code, str | int) and not isinstance(code, bool):
        fields["error_code"] = code
    request_id = response.headers.get("x-request-id")
    if request_id:
        fields["request_id"] = request_id

    links: list[NodeErrorLink] = []
    if status in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
        message = (
            "Autodesk Flow refused the request. Check that the script behind "
            f"{API_KEY_NAME} has permission for this action."
        )
        links = [
            settings_link("Update the API key", API_KEY_NAME),
            NodeErrorLink(label="Script setup", url=SCRIPT_DOCS_URL),
        ]
    elif status == HTTP_NOT_FOUND:
        message = "Autodesk Flow could not find what the request asked for. Check the ID and the entity type."
    elif status == HTTP_RATE_LIMITED:
        message = "Autodesk Flow is rate-limiting requests. Wait a minute and run the node again."
    elif status >= HTTP_SERVER_ERROR:
        message = "Autodesk Flow had a problem handling the request. Wait a moment and run the node again."
    else:
        message = "Autodesk Flow rejected the request."

    if reason:
        message = f"{message} It said: {reason}."
    return NodeError(message, fields=fields, links=links or None, response=body)


def error_from_auth_failure(exc: httpx.HTTPStatusError) -> NodeError:
    """Autodesk Flow refused the script name and API key when asking for an access token."""
    response = exc.response
    body = _response_body(response)
    reason = _reason(_first_api_error(body))
    message = (
        f"Autodesk Flow did not accept the script name and API key. Check {SCRIPT_NAME_NAME} and {API_KEY_NAME} "
        "against the script in Autodesk Flow Admin > Scripts, then run the node again."
    )
    if reason:
        message = f"{message} It said: {reason}."
    return NodeError(
        message,
        fields={"status_code": response.status_code},
        links=[
            settings_link("Update the API key", API_KEY_NAME),
            settings_link("Update the script name", SCRIPT_NAME_NAME),
            NodeErrorLink(label="Script setup", url=SCRIPT_DOCS_URL),
        ],
        response=body,
    )


def error_from_request_failure(exc: httpx.RequestError) -> NodeError:
    host = exc.request.url.host if exc.request is not None else ""
    where = f"Autodesk Flow at {host}" if host else "Autodesk Flow"
    if isinstance(exc, httpx.TimeoutException):
        message = f"{where} did not answer in time. Check the network and run the node again."
    else:
        message = f"Could not connect to {where}. Check {URL_NAME} and the network connection."
    return NodeError(message, links=[settings_link("Check the Autodesk Flow URL", URL_NAME)])


def to_node_error(exc: Exception) -> Exception:
    """Return a NodeError for an Autodesk Flow HTTP failure, and any other exception unchanged."""
    if isinstance(exc, NodeError):
        return exc
    if isinstance(exc, httpx.HTTPStatusError):
        error = error_from_http_status(exc)
    elif isinstance(exc, httpx.RequestError):
        error = error_from_request_failure(exc)
    else:
        return exc
    error.__cause__ = exc
    return error
