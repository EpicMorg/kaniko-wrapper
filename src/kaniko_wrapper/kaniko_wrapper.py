#!/usr/bin/env python3

import os
import shutil
import argparse
import yaml
import subprocess
import time
from collections import defaultdict
from dotenv import load_dotenv
import logging
import sys
import threading
from queue import Queue, Empty
from typing import List, Dict, Any

SCRIPT_VERSION = "3.2.0"

# Lock для синхронизации вывода логов в многопоточном режиме
_log_lock = threading.Lock()

# ASCII art for EpicMorg
ASCII_ART = r"""
+=================================================+
| ____|        _)         \  |                    |
| __|    __ \   |   __|  |\/ |   _ \    __|  _` | |
| |      |   |  |  (     |   |  (   |  |    (   | |
|_____|  .__/  _| \___| _|  _| \___/  _|   \__, | |
| |  /  _|           _)  |                 |___/  |
| ' /    _` |  __ \   |  |  /   _ \               |
| . \   (   |  |   |  |    <   (   |              |
|_|\_\ \__,_| _|  _| _| _|\_\ \___/               |
|\ \        /                                     |
| \ \  \   /   __|  _` |  __ \   __ \    _ \   __||
|  \ \  \ /   |    (   |  |   |  |   |   __/  |   |
|   \_/\_/   _|   \__,_|  .__/   .__/  \___| _|   |
|                        _|     _|                |
+=================================================+
"""

# Load environment variables from .env file
load_dotenv()

def setup_logging():
    """Настройка потокобезопасного логирования."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Убеждаемся, что handler потокобезопасен
    for handler in logging.root.handlers:
        handler.setLevel(logging.INFO)

def create_parser() -> argparse.ArgumentParser:
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(description="EpicMorg: Kaniko-Compose Wrapper", add_help=False)

    # --- Core Flags ---
    parser.add_argument('--compose-file', default=os.getenv('COMPOSE_FILE', 'docker-compose.yml'), help='Path to docker-compose.yml file')
    parser.add_argument('--version', '-v', action='store_true', help='Show script version')
    parser.add_argument('--help', '-h', action='store_true', help='Show this help message and exit')

    # --- Control Flags ---
    parser.add_argument('--engine', default='podman', choices=['podman', 'docker'], help='Container engine to use (default: podman)')
    parser.add_argument('--network', default='host', help='Network mode. (default: host)')

    # --- Command Flags ---
    parser.add_argument('--push', '--deploy', '-d', '-p', action='store_true', help='Push the built images to the registry (and mirrors)')
    parser.add_argument('--dry-run', '--dry', action='store_true', help='Build images without pushing (adds --no-push)')

    # --- Kaniko Flags ---
    kaniko_group = parser.add_argument_group('Kaniko Arguments')
    kaniko_group.add_argument('--kaniko-image', default=os.getenv('KANIKO_IMAGE', 'gcr.io/kaniko-project/executor:latest'), help='Kaniko executor image')
    kaniko_group.add_argument('--skopeo-image', default='quay.io/skopeo/skopeo:latest', help='Skopeo image for mirroring')
    kaniko_group.add_argument('--push-retry', default='7', help='Kaniko --push-retry count')
    kaniko_group.add_argument('--snapshot-mode', default='full', help='Kaniko --snapshot-mode (default: full)')
    kaniko_group.add_argument('--log-timestamp', action='store_true', default=False, help='Enable Kaniko --log-timestamp (default: false)')
    kaniko_group.add_argument('--cache', action='store_true', default=False, help='Enable Kaniko cache (default: false)')
    kaniko_group.add_argument('--use-new-run', action='store_true', default=True, help='Enable Kaniko --use-new-run (default: true)')
    kaniko_group.add_argument('--no-cleanup', action='store_true', default=False, help='Disable Kaniko --cleanup flag (default: cleanup=true)')
    kaniko_group.add_argument('--single-snapshot', action='store_true', default=True, help='Enable Kaniko --single-snapshot (default: true)')

    return parser

def load_compose_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def _run_command_stream(cmd: List[str], service_name: str) -> bool:
    """
    Helper for running a command and streaming its logs.
    Uses a queue to synchronize output from stdout and stderr threads.
    """
    with _log_lock:
        logging.info(f"[{service_name}] Executing: {' '.join(cmd)}")

    # Use Popen with separate stdout/stderr pipes
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Queue for synchronizing log output
    log_queue = Queue()

    def read_stdout():
        """Read stdout lines and put them in queue."""
        if process.stdout:
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # Strip whitespace and control characters to prevent formatting issues
                        cleaned_line = line.strip()
                        if cleaned_line:  # Only add non-empty lines
                            log_queue.put(('info', cleaned_line))
                log_queue.put(('stdout_done', None))
            except Exception as e:
                log_queue.put(('error', f"Error reading stdout: {e}"))

    def read_stderr():
        """Read stderr lines and put them in queue."""
        if process.stderr:
            try:
                for line in iter(process.stderr.readline, ''):
                    if line:
                        # Strip whitespace and control characters to prevent formatting issues
                        cleaned_line = line.strip()
                        if cleaned_line:  # Only add non-empty lines
                            log_queue.put(('error', cleaned_line))
                log_queue.put(('stderr_done', None))
            except Exception as e:
                log_queue.put(('error', f"Error reading stderr: {e}"))

    def log_worker():
        """Single thread that logs all messages from queue."""
        stdout_done = False
        stderr_done = False
        
        while True:
            try:
                msg_type, message = log_queue.get(timeout=0.1)
                
                if msg_type == 'stdout_done':
                    stdout_done = True
                elif msg_type == 'stderr_done':
                    stderr_done = True
                elif msg_type == 'info':
                    with _log_lock:
                        logging.info(f"[{service_name}] {message}")
                elif msg_type == 'error':
                    with _log_lock:
                        logging.error(f"[{service_name}] {message}")
                
                # Check if both streams are done and queue is empty
                if stdout_done and stderr_done and log_queue.empty():
                    break
            except Empty:
                # If both streams are done and queue is empty, exit
                if stdout_done and stderr_done:
                    break
                continue

    # Start threads for reading
    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    log_thread = threading.Thread(target=log_worker, daemon=True)
    
    stdout_thread.start()
    stderr_thread.start()
    log_thread.start()

    # Wait for process to complete
    process.wait()

    # Wait for threads to finish reading remaining data
    stdout_thread.join(timeout=3.0)
    stderr_thread.join(timeout=3.0)
    
    # Wait for log thread to process all remaining messages
    log_thread.join(timeout=2.0)

    with _log_lock:
        if process.returncode == 0:
            return True
        else:
            logging.error(f"[{service_name}] Command failed with code {process.returncode}")
            return False

def _run_skopeo_copy(source_image: str, dest_image: str, cli_args: argparse.Namespace, docker_config_dir: str, service_name: str):
    """
    Run 'skopeo copy' inside container.
    """
    skopeo_command = [cli_args.engine, 'run']
    skopeo_command.append(f'--network={cli_args.network}')
    skopeo_command.extend(['--rm'])
    skopeo_command.extend(['-v', f'{docker_config_dir}:/root/.docker:ro'])
    skopeo_command.extend([
        cli_args.skopeo_image,
        'copy',
        '--all',
        f'docker://{source_image}',
        f'docker://{dest_image}'
    ])

    if not _run_command_stream(skopeo_command, f"{service_name}-mirror"):
        with _log_lock:
            logging.error(f"[{service_name}] Failed to mirror {source_image} to {dest_image}")
    else:
        with _log_lock:
            logging.info(f"[{service_name}] Successfully mirrored to {dest_image}")


def build_and_mirror_task(
    service_name: str,
    build_context: str,
    dockerfile: str,
    image_name: str,
    build_args: Dict[str, str],
    mirrors: List[str],
    cli_args: argparse.Namespace
):
    """
    A single worker task that:
    1. Builds an image via Kaniko.
    2. If --push, pushes to mirrors via Skopeo.
    """
    docker_config_dir = os.path.expanduser("~/.docker")
    abs_build_context = os.path.abspath(build_context)

    kaniko_command = [cli_args.engine, 'run']
    kaniko_command.append(f'--network={cli_args.network}')
    kaniko_command.extend(['--rm'])
    kaniko_command.extend([
        '-v', f'{abs_build_context}:/workspace',
        '-v', f'{docker_config_dir}:/kaniko/.docker:ro',
    ])
    kaniko_command.append(cli_args.kaniko_image)
    kaniko_command.extend([
        '--context', '/workspace',
        '--dockerfile', f'/workspace/{dockerfile}',
        f'--push-retry={cli_args.push_retry}',
        f'--snapshot-mode={cli_args.snapshot_mode}',
    ])

    if cli_args.use_new_run:
        kaniko_command.append('--use-new-run')
    if cli_args.log_timestamp:
        kaniko_command.append('--log-timestamp')
    if cli_args.cache:
        kaniko_command.append('--cache=true')
    else:
        kaniko_command.append('--cache=false')
    if not cli_args.no_cleanup:
        kaniko_command.append('--cleanup')
    if cli_args.single_snapshot:
        kaniko_command.append('--single-snapshot')

    if cli_args.push:
        kaniko_command.extend(['--destination', image_name])
    else:
        kaniko_command.append('--no-push')

    for arg_name, arg_value in build_args.items():
        kaniko_command.extend(['--build-arg', f'{arg_name}={arg_value}'])

    # --- Run Kaniko ---
    if not _run_command_stream(kaniko_command, service_name):
        raise Exception(f"Failed to build {service_name}")

    with _log_lock:
        logging.info(f"Successfully built {service_name}")

    # --- Run Skopeo (Mirroring) ---
    if cli_args.push and mirrors:
        with _log_lock:
            logging.info(f"[{service_name}] Build successful. Mirroring to {len(mirrors)} destinations...")
        for mirror in mirrors:
            _run_skopeo_copy(image_name, mirror, cli_args, docker_config_dir, service_name)


def show_help(parser: argparse.ArgumentParser):
    """Prints the custom ASCII art and the parser's help."""
    print(ASCII_ART)
    print(f"EpicMorg: Kaniko-Compose Wrapper v{SCRIPT_VERSION}\n")
    parser.print_help()

def show_version():
    print(ASCII_ART)
    print(f"EpicMorg: Kaniko-Compose Wrapper {SCRIPT_VERSION}, Python: {sys.version}")

def main():
    setup_logging()

    parser = create_parser()
    args = parser.parse_args()

    if args.help:
        show_help(parser)
        return

    if args.version:
        show_version()
        return

    action_specified = any([
        args.push,
        args.dry_run,
        args.compose_file != os.getenv('COMPOSE_FILE', 'docker-compose.yml')
    ])

    if not action_specified:
        show_version()
        return

    compose_file = args.compose_file

    if not os.path.exists(compose_file):
        logging.error(f"{compose_file} not found")
        sys.exit(1)

    compose_data = load_compose_file(compose_file)
    services = compose_data.get('services', {})
    image_names = defaultdict(int)

    for service_name, service_data in services.items():
        if not service_data:
            logging.warning(f"Service {service_name} is empty (null), skipping.")
            continue
        image_name = service_data.get('image')
        if not image_name:
            logging.warning(f"No image specified for service {service_name}, skipping.")
            continue
        image_names[image_name] += 1

    for image_name, count in image_names.items():
        if count > 1:
            logging.error(f"Error: Image name {image_name} is used {count} times.")
            return

    # --- Последовательное выполнение всех сервисов ---
    try:
        service_list = []

        for service_name, service_data in services.items():
            if not service_data: continue
            build_data = service_data.get('build', {})
            if not build_data:
                logging.warning(f"No 'build' section for service {service_name}, skipping.")
                continue
            build_context = build_data.get('context', '.')
            dockerfile = build_data.get('dockerfile', 'Dockerfile')
            image_name = service_data.get('image')
            if not image_name:
                logging.warning(f"No image specified for service {service_name}, skipping.")
                continue
            build_args = build_data.get('args', {})
            build_args = {key: os.getenv(key, str(value)) for key, value in build_args.items()}
            mirrors = service_data.get('x-mirrors', [])

            service_list.append((
                service_name,
                build_context,
                dockerfile,
                image_name,
                build_args,
                mirrors
            ))

        if not service_list:
            logging.warning("No services to build.")
            return

        logging.info(f"Starting build of {len(service_list)} service(s) sequentially using {args.engine} engine...")

        for service_name, build_context, dockerfile, image_name, build_args, mirrors in service_list:
            try:
                build_and_mirror_task(
                    service_name,
                    build_context,
                    dockerfile,
                    image_name,
                    build_args,
                    mirrors,
                    args
                )
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                logging.error(f"Failed to build {service_name}: {exc}")
                raise

    except KeyboardInterrupt:
        with _log_lock:
            logging.warning("Build interrupted by user.")
        sys.exit(130)
    except Exception as exc:
        with _log_lock:
            logging.error(f"Build failed: {exc}")
        sys.exit(1)

if __name__ == '__main__':
    main()
