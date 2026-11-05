import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest
from griptape_nodes.exe_types.core_types import NodeError
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

LIBRARY_DIR = Path(__file__).resolve().parents[2] / "flow_production_tracking"
MANIFEST = LIBRARY_DIR / "griptape_nodes_library.json"


class FakeSecrets:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def get_secret(self, name: str, *, should_error_on_not_found: bool = True) -> str | None:  # noqa: ARG002
        return self.values.get(name)


@pytest.fixture
def secrets(monkeypatch: pytest.MonkeyPatch):
    values: dict[str, str] = {}
    monkeypatch.setattr(GriptapeNodes, "SecretsManager", lambda: FakeSecrets(values))
    return values


def _status_error(status: int, body: dict | str, headers: dict | None = None) -> httpx.HTTPStatusError:
    """Send a real request through httpx and let raise_for_status build the error."""

    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(body, str):
            return httpx.Response(status, text=body, headers=headers)
        return httpx.Response(status, json=body, headers=headers)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        response = client.get("https://studio.shotgrid.autodesk.com/api/v1/entity/projects/1")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return exc
    msg = "expected an HTTP error"
    raise AssertionError(msg)


def test_http_error_carries_reason_status_and_response():
    from flow_node_errors import to_node_error

    body = {"errors": [{"status": 404, "code": 104, "title": "Not found", "detail": "Project 99 does not exist."}]}
    error = to_node_error(_status_error(404, body, {"x-request-id": "req-1"}))

    assert isinstance(error, NodeError)
    assert "Project 99 does not exist" in str(error)
    assert error.fields == {"status_code": 404, "error_code": 104, "request_id": "req-1"}
    assert error.response == body
    assert "studio.shotgrid" not in str(error)
    assert "mozilla" not in str(error)


def test_refused_request_links_to_the_key():
    from flow_node_errors import to_node_error

    error = to_node_error(_status_error(403, {"errors": [{"title": "Forbidden"}]}))

    assert isinstance(error, NodeError)
    assert error.links
    assert error.links[0].url == "#settings-secrets?filter=SHOTGRID_API_KEY"


def test_non_json_error_body_is_kept():
    from flow_node_errors import to_node_error

    error = to_node_error(_status_error(502, "Bad gateway"))

    assert isinstance(error, NodeError)
    assert error.response == {"body": "Bad gateway"}
    assert error.fields == {"status_code": 502}


def test_connection_failure_links_to_the_url_setting():
    from flow_node_errors import to_node_error

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns failure", request=request)

    with pytest.raises(httpx.ConnectError) as caught, httpx.Client(transport=httpx.MockTransport(handler)) as client:
        client.get("https://nowhere.example.com/api/v1/entity/projects")

    error = to_node_error(caught.value)
    assert isinstance(error, NodeError)
    assert "nowhere.example.com" in str(error)
    assert error.links[0].url == "#settings-secrets?filter=SHOTGRID_URL"


def test_other_exceptions_pass_through():
    from flow_node_errors import to_node_error

    original = KeyError("x")
    assert to_node_error(original) is original


def test_parameter_label():
    from flow_node_errors import parameter_label

    assert parameter_label("project_id") == "Project ID"
    assert parameter_label("entity_type") == "Entity Type"


def test_missing_credentials_are_reported_alone(secrets):
    from flow_get_project import FlowGetProject

    node = FlowGetProject(name="node")
    errors = node.validate_before_node_run()

    assert errors is not None
    assert len(errors) == 2
    assert all(isinstance(e, NodeError) for e in errors)
    assert "SHOTGRID_API_KEY" in str(errors[0])
    assert "SHOTGRID_URL" in str(errors[1])


def test_credentials_present_passes_validation(secrets):
    from flow_get_project import FlowGetProject

    secrets.update({"SHOTGRID_API_KEY": "k", "SHOTGRID_URL": "https://studio.shotgrid.autodesk.com"})
    assert FlowGetProject(name="node").validate_before_node_run() is None


def test_file_path_node_needs_no_credentials(secrets):
    from flow_get_file_path import FlowGetFilePath

    assert FlowGetFilePath(name="node").validate_before_node_run() is None


def test_missing_input_raises_when_failed_is_unwired(secrets):
    from flow_get_project import FlowGetProject

    secrets.update({"SHOTGRID_API_KEY": "k", "SHOTGRID_URL": "https://studio.shotgrid.autodesk.com"})
    node = FlowGetProject(name="node")
    node._has_outgoing_connections = lambda _param: False  # type: ignore[method-assign]

    with pytest.raises(NodeError, match="'Project ID' is required"):
        node._do_process()


def test_missing_input_follows_failed_when_wired(secrets):
    from flow_get_project import FlowGetProject

    secrets.update({"SHOTGRID_API_KEY": "k", "SHOTGRID_URL": "https://studio.shotgrid.autodesk.com"})
    node = FlowGetProject(name="node")
    node._has_outgoing_connections = lambda _param: True  # type: ignore[method-assign]

    node._do_process()

    assert node.parameter_output_values["was_successful"] is False
    assert "'Project ID' is required" in node.parameter_output_values["result_details"]


def test_non_integer_project_id_names_the_value(secrets):
    from flow_get_project import FlowGetProject

    secrets.update({"SHOTGRID_API_KEY": "k", "SHOTGRID_URL": "https://studio.shotgrid.autodesk.com"})
    node = FlowGetProject(name="node")
    node.set_parameter_value("project_id", "abc")
    node._has_outgoing_connections = lambda _param: False  # type: ignore[method-assign]

    with pytest.raises(NodeError, match="'Project ID' must be a whole number.*'abc'"):
        node._do_process()


def test_rejected_sign_in_links_to_key_and_script_name(secrets, monkeypatch: pytest.MonkeyPatch):
    import base_shotgrid_node
    from flow_get_project import FlowGetProject

    secrets.update({"SHOTGRID_API_KEY": "k", "SHOTGRID_URL": "https://studio.shotgrid.autodesk.com"})
    body = {"errors": [{"status": 400, "title": "Can't authenticate script 'gtn'."}]}
    exc = _status_error(400, body)

    def fake_post(*_args, **_kwargs):
        response = exc.response
        response.request = exc.request
        return response

    monkeypatch.setattr(base_shotgrid_node.httpx, "post", fake_post)
    node = FlowGetProject(name="node")

    with pytest.raises(NodeError) as caught:
        node._get_access_token()

    urls = [link.url for link in caught.value.links]
    assert "#settings-secrets?filter=SHOTGRID_API_KEY" in urls
    assert "#settings-secrets?filter=SHOTGRID_SCRIPT_NAME" in urls
    assert caught.value.response == body


def test_node_files_load_the_way_the_engine_loads_them(monkeypatch: pytest.MonkeyPatch):
    """The engine loads each node file alone, with the library folder on sys.path and no package."""
    manifest = json.loads(MANIFEST.read_text())
    monkeypatch.syspath_prepend(str(LIBRARY_DIR))
    monkeypatch.setitem(sys.modules, "flow_production_tracking", None)  # type: ignore[arg-type]

    for node in manifest["nodes"]:
        file_path = LIBRARY_DIR / node["file_path"]
        module_name = f"_engine_style_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, module_name, module)
        spec.loader.exec_module(module)
        assert hasattr(module, node["class_name"])
