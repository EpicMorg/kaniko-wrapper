import os
import yaml
import pytest
from unittest.mock import patch, MagicMock

from kaniko_wrapper.helper.class_kaniko import (
    ComposeFileLoader,
    KanikoBuilder,
    BuildKaniko,
)
from kaniko_wrapper.helper._dataclass import KanikoBuildError


def _builder(**args_overrides):
    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    args.kaniko_image = "ghcr.io/osscontainertools/kaniko:latest"
    for k, v in args_overrides.items():
        setattr(args, k, v)
    return KanikoBuilder(args)


# --- ComposeFileLoader -------------------------------------------------------


@pytest.fixture
def create_test_file():
    test_file_path = "test_compose_file.yaml"
    with open(test_file_path, "w") as file:
        yaml.dump({"key": "value"}, file)
    yield test_file_path
    if os.path.exists(test_file_path):
        os.remove(test_file_path)


def test_load_raises_when_file_does_not_exist():
    loader = ComposeFileLoader("non_existent_compose_file.yaml")
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_load_returns_data_when_file_exists(create_test_file):
    loader = ComposeFileLoader(create_test_file)
    assert loader.load() == {"key": "value"}


# --- validate_compose_file ---------------------------------------------------


@patch("kaniko_wrapper.helper.class_kaniko.ComposeFileLoader")
@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_validate_compose_file(mock_logger, mock_loader):
    mock_loader.return_value.load.return_value = {"services": {}}

    builder = _builder()
    builder.validate_compose_file()

    mock_loader.return_value.load.assert_called_once()
    mock_logger.info.assert_called_once_with(
        "Successfully loaded compose file: docker-compose.yml"
    )


@patch("kaniko_wrapper.helper.class_kaniko.ComposeFileLoader")
@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_validate_compose_file_error(mock_logger, mock_loader):
    mock_loader.return_value.load.side_effect = Exception("Invalid compose file")

    builder = _builder()
    with pytest.raises(Exception):
        builder.validate_compose_file()

    mock_logger.error.assert_called_once_with(
        "Error loading compose file: Invalid compose file"
    )


# --- process_services --------------------------------------------------------


def test_process_services():
    builder = _builder()
    builder.compose_data = {
        "services": {
            "service1": {
                "build": {"dockerfile": "Dockerfile1", "context": "context1", "args": {"ARG1": "value1"}},
                "image": "image1",
            },
            "service2": {
                "build": {"dockerfile": "Dockerfile2", "context": "context2", "args": {"ARG2": "value2"}},
                "image": "image2",
            },
        }
    }

    builder.process_services()

    assert len(builder.services) == 2
    assert all(isinstance(s, BuildKaniko) for s in builder.services)
    assert [s.service_name for s in builder.services] == ["service1", "service2"]
    assert builder.services[0].engine == "docker"


@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_process_services_no_services(mock_logger):
    builder = _builder()
    builder.compose_data = {}

    with pytest.raises(ValueError):
        builder.process_services()

    mock_logger.error.assert_called_once_with("No services found in docker-compose file.")


def test_process_services_skips_empty_and_pull_only():
    builder = _builder()
    builder.compose_data = {
        "services": {
            "empty": None,  # empty definition -> skip
            "external": {"image": "redis:7"},  # no build section -> skip
            "app": {"build": {"context": "."}, "image": "app:latest"},
        }
    }

    builder.process_services()

    assert [s.service_name for s in builder.services] == ["app"]


def test_process_services_parses_x_mirrors():
    builder = _builder()
    builder.compose_data = {
        "services": {
            "app": {
                "build": {"context": "."},
                "image": "docker.io/epicmorg/app:latest",
                "x-mirrors": ["quay.io/epicmorg/app:latest"],
            }
        }
    }

    builder.process_services()

    assert builder.services[0].mirrors == ["quay.io/epicmorg/app:latest"]


def test_process_services_x_mirrors_must_be_list():
    builder = _builder()
    builder.compose_data = {
        "services": {
            "app": {
                "build": {"context": "."},
                "image": "app:latest",
                "x-mirrors": "quay.io/app:latest",  # string -> hard fail
            }
        }
    }

    with pytest.raises(ValueError):
        builder.process_services()


def test_process_services_short_form_build_rejected():
    builder = _builder()
    builder.compose_data = {
        "services": {"app": {"build": "./app", "image": "app:latest"}}
    }

    with pytest.raises(ValueError):
        builder.process_services()


# --- ensure_executor ---------------------------------------------------------


@patch("kaniko_wrapper.helper.class_kaniko.subprocess.run")
def test_ensure_executor_present_skips_pull(mock_run):
    mock_run.return_value = MagicMock(returncode=0)  # image inspect succeeds

    _builder().ensure_executor()

    mock_run.assert_called_once()  # only inspect, no pull


@patch("kaniko_wrapper.helper.class_kaniko.subprocess.run")
def test_ensure_executor_pulls_when_missing(mock_run):
    mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]  # miss, then pull ok

    _builder().ensure_executor()

    assert mock_run.call_count == 2


@patch("kaniko_wrapper.helper.class_kaniko.subprocess.run")
def test_ensure_executor_raises_on_pull_failure(mock_run):
    mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=1)]  # miss, pull fails

    with pytest.raises(RuntimeError):
        _builder().ensure_executor()


# --- build_services ----------------------------------------------------------


@patch("kaniko_wrapper.helper.class_kaniko.KanikoBuilder.ensure_executor")
def test_build_services_runs_all(mock_ensure):
    s1, s2 = MagicMock(), MagicMock()
    builder = _builder()
    builder.services = [s1, s2]

    builder.build_services()

    mock_ensure.assert_called_once()
    s1.build.assert_called_once()
    s2.build.assert_called_once()


@patch("kaniko_wrapper.helper.class_kaniko.KanikoBuilder.ensure_executor")
def test_build_services_aggregates_failures(mock_ensure):
    s1 = MagicMock(service_name="s1")
    s1.build.side_effect = KanikoBuildError("boom")
    s2 = MagicMock(service_name="s2")

    builder = _builder()
    builder.services = [s1, s2]

    with pytest.raises(KanikoBuildError):
        builder.build_services()

    # aggregate-continue: s2 is still attempted after s1 fails
    s1.build.assert_called_once()
    s2.build.assert_called_once()