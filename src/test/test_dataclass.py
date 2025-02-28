import sys
import pytest
from unittest.mock import patch, MagicMock

from kaniko_wrapper.helper._dataclass import ArgParser
from kaniko_wrapper.helper.class_kaniko import BuildKaniko


@pytest.fixture
def restore_sys_argv():
    original_argv = sys.argv
    yield
    sys.argv = original_argv


def test_argparser_default_compose_file(restore_sys_argv):
    test_args = ["prog"]
    sys.argv = test_args
    arg_parser = ArgParser()
    args = arg_parser.parse_args()
    assert (
        args.compose_file == "docker-compose.yml"
    ), "Default compose file should be 'docker-compose.yml'"


def test_argparser_dry_run_flag(restore_sys_argv):
    test_args = ["prog", "--dry-run"]
    sys.argv = test_args
    arg_parser = ArgParser()
    args = arg_parser.parse_args()
    assert args.dry_run is True, "--dry-run flag should be set"


def test_generate_kaniko_command():
    build_kaniko = BuildKaniko(
        service_name="test_service",
        build_context="path/to/context",
        dockerfile="Dockerfile",
        image_name="test_image",
        build_args={"ARG1": "value1", "ARG2": "value2"},
        kaniko_image="gcr.io/kaniko-project/executor:latest",
        deploy=True,
        dry=False,
        no_push=False,
    )

    command = build_kaniko._generate_kaniko_command()

    assert "docker" in command[0]
    assert "--rm" in command
    assert "--destination" in command
    assert "--build-arg ARG1=value1" in command
    assert "--build-arg ARG2=value2" in command
    assert "test_image" in command


def test_generate_kaniko_command_no_push():
    build_kaniko = BuildKaniko(
        service_name="test_service",
        build_context="path/to/context",
        dockerfile="Dockerfile",
        image_name="test_image",
        build_args={"ARG1": "value1"},
        kaniko_image="gcr.io/kaniko-project/executor:latest",
        deploy=False,
        dry=False,
        no_push=True,
    )

    command = build_kaniko._generate_kaniko_command()
    assert "--no-push" in command


@patch("subprocess.Popen")
def test_build_failure(mock_popen):
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_popen.return_value = mock_process

    build_kaniko = BuildKaniko(
        service_name="test_service",
        build_context="path/to/context",
        dockerfile="Dockerfile",
        image_name="test_image",
        build_args={},
        kaniko_image="gcr.io/kaniko-project/executor:latest",
        deploy=True,
        dry=False,
        no_push=False,
    )

    with pytest.raises(Exception):
        build_kaniko.build()
