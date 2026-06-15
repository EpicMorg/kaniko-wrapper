import io
import sys
import pytest
from unittest.mock import patch, MagicMock

from kaniko_wrapper.helper._dataclass import ArgParser, BuildKaniko, KanikoBuildError


@pytest.fixture
def restore_sys_argv():
    original_argv = sys.argv
    yield
    sys.argv = original_argv


def _make_build(**overrides):
    base = dict(
        service_name="test_service",
        build_context="path/to/context",
        dockerfile="Dockerfile",
        image_name="test_image",
        build_args={},
        kaniko_image="ghcr.io/osscontainertools/kaniko:latest",
        deploy=True,
        dry=False,
        no_push=False,
    )
    base.update(overrides)
    return BuildKaniko(**base)


def _destinations(command):
    return [command[i + 1] for i, tok in enumerate(command) if tok == "--destination"]


# --- ArgParser ---------------------------------------------------------------


def test_argparser_default_compose_file(restore_sys_argv):
    sys.argv = ["prog"]
    args = ArgParser().parse_args()
    assert args.compose_file == "docker-compose.yml"


def test_argparser_default_kaniko_image(restore_sys_argv, monkeypatch):
    monkeypatch.delenv("KANIKO_IMAGE", raising=False)
    sys.argv = ["prog"]
    args = ArgParser().parse_args()
    assert args.kaniko_image == "ghcr.io/osscontainertools/kaniko:latest"


def test_argparser_dry_run_flag(restore_sys_argv):
    sys.argv = ["prog", "--dry-run"]
    args = ArgParser().parse_args()
    assert args.dry_run is True


def test_argparser_verbose_flag(restore_sys_argv):
    # Requires the --verbose/-V argument added to ArgParser.
    sys.argv = ["prog", "--verbose"]
    args = ArgParser().parse_args()
    assert args.verbose is True


def test_argparser_log_level(restore_sys_argv):
    # Requires the --log-level argument added to ArgParser.
    sys.argv = ["prog", "--log-level", "DEBUG"]
    args = ArgParser().parse_args()
    assert args.log_level == "DEBUG"


# --- _generate_kaniko_command ------------------------------------------------


def test_generate_kaniko_command():
    command = _make_build(build_args={"ARG1": "value1", "ARG2": "value2"})._generate_kaniko_command()

    assert command[0] == "docker"  # default engine
    assert "--rm" in command
    assert "-t" not in command  # removed: no TTY with piped output
    assert "--destination" in command
    assert "test_image" in command
    assert command.count("--build-arg") == 2
    assert "ARG1=value1" in command
    assert "ARG2=value2" in command


def test_generate_kaniko_command_no_push():
    command = _make_build(deploy=False, no_push=True)._generate_kaniko_command()
    assert "--no-push" in command
    assert "--destination" not in command


def test_generate_kaniko_command_custom_engine():
    command = _make_build(engine="podman")._generate_kaniko_command()
    assert command[0] == "podman"


def test_generate_kaniko_command_mirrors_dedup_and_order():
    command = _make_build(
        image_name="docker.io/epicmorg/app:latest",
        mirrors=[
            "quay.io/epicmorg/app:latest",
            "docker.io/epicmorg/app:latest",  # duplicate of primary -> dropped
            "  ",  # empty after strip -> dropped
        ],
    )._generate_kaniko_command()

    # Primary first, then unique mirrors; duplicate and blank removed.
    assert _destinations(command) == [
        "docker.io/epicmorg/app:latest",
        "quay.io/epicmorg/app:latest",
    ]


# --- build() -----------------------------------------------------------------


@patch("kaniko_wrapper.helper._dataclass.subprocess.Popen")
@patch("kaniko_wrapper.helper._dataclass.os.path.exists", return_value=True)
def test_build_raises_on_nonzero_returncode(mock_exists, mock_popen):
    process = MagicMock()
    process.stdout = io.StringIO("")
    process.stderr = io.StringIO("error: failed to push\n")
    process.wait.return_value = 1
    mock_popen.return_value = process

    with pytest.raises(KanikoBuildError):
        _make_build().build()


@patch("kaniko_wrapper.helper._dataclass.subprocess.Popen")
@patch("kaniko_wrapper.helper._dataclass.os.path.exists", return_value=True)
def test_build_succeeds_on_zero_returncode(mock_exists, mock_popen):
    process = MagicMock()
    process.stdout = io.StringIO("step 1/3\nstep 2/3\n")
    process.stderr = io.StringIO("")
    process.wait.return_value = 0
    mock_popen.return_value = process

    # Should not raise.
    _make_build().build()


def test_build_raises_when_context_missing():
    # Real path that does not exist -> FileNotFoundError before any subprocess.
    with pytest.raises(FileNotFoundError):
        _make_build(build_context="definitely/missing/path").build()