import os
import yaml
import pytest
from unittest.mock import patch, MagicMock

from kaniko_wrapper.helper.class_kaniko import ComposeFileLoader
from kaniko_wrapper.helper.class_kaniko import KanikoBuilder, BuildKaniko


@pytest.fixture
def create_test_file():
    test_file_path = "test_compose_file.yaml"
    with open(test_file_path, "w") as file:
        yaml.dump({"key": "value"}, file)
    yield test_file_path
    if os.path.exists(test_file_path):
        os.remove(test_file_path)


def test_load_raises_when_file_does_not_exist():
    non_existent_file = "non_existent_compose_file.yaml"
    loader = ComposeFileLoader(non_existent_file)
    with pytest.raises(FileNotFoundError):
        loader.load()


def test_load_returns_data_when_file_exists(create_test_file):
    loader = ComposeFileLoader(create_test_file)
    data = loader.load()
    assert data == {"key": "value"}


@patch("kaniko_wrapper.helper.class_kaniko.ComposeFileLoader")
@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_validate_compose_file(mock_logger, mock_loader):
    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = {"services": {}}
    mock_loader.return_value = mock_loader_instance

    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    builder = KanikoBuilder(args)

    builder.validate_compose_file()

    mock_loader_instance.load.assert_called_once()
    mock_logger.info.assert_called_once_with(
        "Successfully loaded compose file: docker-compose.yml"
    )


@patch("kaniko_wrapper.helper.class_kaniko.ComposeFileLoader")
@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_validate_compose_file_error(mock_logger, mock_loader):
    mock_loader.return_value.load.side_effect = Exception("Invalid compose file")

    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    builder = KanikoBuilder(args)

    with pytest.raises(Exception):
        builder.validate_compose_file()

    mock_logger.error.assert_called_once_with(
        "Error loading compose file: Invalid compose file"
    )


def test_process_services():
    mock_services_data = {
        "service1": {
            "build": {
                "dockerfile": "Dockerfile1",
                "context": "context1",
                "args": {"ARG1": "value1"},
            },
            "image": "image1",
        },
        "service2": {
            "build": {
                "dockerfile": "Dockerfile2",
                "context": "context2",
                "args": {"ARG2": "value2"},
            },
            "image": "image2",
        },
    }

    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    args.kaniko_image = "gcr.io/kaniko-project/executor:latest"
    builder = KanikoBuilder(args)

    builder.compose_data = {"services": mock_services_data}

    builder.process_services()

    assert len(builder.services) == 2
    assert isinstance(builder.services[0], BuildKaniko)
    assert builder.services[0].service_name == "service1"
    assert builder.services[1].service_name == "service2"


@patch("kaniko_wrapper.helper.class_kaniko.logger")
def test_process_services_no_services(mock_logger):
    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    builder = KanikoBuilder(args)

    builder.compose_data = {}

    with pytest.raises(Exception):
        builder.process_services()

    mock_logger.error.assert_called_once_with(
        "No services found in docker-compose file."
    )


@patch("kaniko_wrapper.helper.class_kaniko.BuildKaniko")
def test_build_services(mock_build_kaniko):
    mock_service1 = MagicMock()
    mock_service2 = MagicMock()
    mock_build_kaniko.return_value = mock_service1
    mock_build_kaniko.return_value = mock_service2

    args = MagicMock()
    args.compose_file = "docker-compose.yml"
    args.kaniko_image = "gcr.io/kaniko-project/executor:latest"
    builder = KanikoBuilder(args)

    builder.services = [mock_service1, mock_service2]

    builder.build_services()

    mock_service1.build.assert_called_once()
    mock_service2.build.assert_called_once()
