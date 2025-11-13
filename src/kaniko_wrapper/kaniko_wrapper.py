#!/usr/bin/env python3

import os
import shutil
import argparse
import yaml
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import logging
import sys
from typing import List, Dict, Any


SCRIPT_VERSION = "3.0.0"

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_args():
    parser = argparse.ArgumentParser(description="EpicMorg: Kaniko-Compose Wrapper", add_help=False)
    
    
    parser.add_argument('--compose-file', default=os.getenv('COMPOSE_FILE', 'docker-compose.yml'), help='Path to docker-compose.yml file')
    parser.add_argument('--version', '-v', action='store_true', help='Show script version')
    parser.add_argument('--help', '-h', action='store_true', help='Show this help message and exit')
    
    
    parser.add_argument('--engine', default='podman', choices=['podman', 'docker'], help='Container engine to use (default: podman)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel build workers (default: 4)')
    parser.add_argument('--network', default='host', help='Network mode. (default: host)')
    
    
    parser.add_argument('--push', '--deploy', '-d', '-p', action='store_true', help='Push the built images to the registry (and mirrors)')
    parser.add_argument('--dry-run', '--dry', action='store_true', help='Build images without pushing (adds --no-push)')

    
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
    
    return parser.parse_args()

def load_compose_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def _run_command_stream(cmd: List[str], service_name: str) -> bool:
    """Helper for running a command and streaming its logs."""
    logging.info(f"[{service_name}] Executing: {' '.join(cmd)}")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Стрим output
    for line in process.stdout:
        logging.info(f"[{service_name}] {line.strip()}")
    
    process.wait()
    
    if process.returncode == 0:
        return True
    else:
        
        for line in process.stderr:
            logging.error(f"[{service_name}] {line.strip()}")
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
        
        logging.error(f"[{service_name}] Failed to mirror {source_image} to {dest_image}")
    else:
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

    kaniko_command.extend(['--rm', '-t'])

    
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
    
    
    if not _run_command_stream(kaniko_command, service_name):
        raise Exception(f"Failed to build {service_name}")
    
    logging.info(f"Successfully built {service_name}")

    
    if cli_args.push and mirrors:
        logging.info(f"[{service_name}] Build successful. Mirroring to {len(mirrors)} destinations...")
        for mirror in mirrors:
            
            _run_skopeo_copy(image_name, mirror, cli_args, docker_config_dir, service_name)


def show_help():
    print(ASCII_ART)
    print(f"EpicMorg: Kaniko-Compose Wrapper v{SCRIPT_VERSION}\n")
    
    argparse.ArgumentParser(description=f"Kaniko Wrapper v{SCRIPT_VERSION}").print_help()
    
def show_version():
    print(ASCII_ART)
    print(f"EpicMorg: Kaniko-Compose Wrapper {SCRIPT_VERSION}, Python: {sys.version}")

def main():
    setup_logging()
    
    args = parse_args()

    if args.help:
        show_help()
        return
    
    if args.version:
        show_version()
        return
    
    
    
    compose_file = args.compose_file
    
    if not os.path.exists(compose_file):
        logging.error(f"{compose_file} not found")
        return
    
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
    
    try:
        
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            logging.info(f"Starting build with max {args.workers} workers using {args.engine} engine...")
            futures = []
            
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
                
                futures.append(executor.submit(
                    build_and_mirror_task, 
                    service_name, 
                    build_context, 
                    dockerfile, 
                    image_name, 
                    build_args, 
                    mirrors, 
                    args  
                ))
            
            for future in as_completed(futures):
                future.result() 

    except Exception as exc:
        logging.error(f"Build failed: {exc}")
        sys.exit(1)

if __name__ == '__main__':
    main()
 