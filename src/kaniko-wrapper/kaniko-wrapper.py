import os
import yaml
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import logging

load_dotenv()

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_compose_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def build_with_kaniko(service_name, build_context, dockerfile, image_name, build_args, kaniko_image):
    kaniko_command = [
        'docker', 'run',
        '--rm',
        '-v', f'{os.path.abspath(build_context)}:/workspace',
        '-v', '/var/run/docker.sock:/var/run/docker.sock', 
        '-v', f'{os.path.expanduser("~")}/.docker:/root/.docker', 
        kaniko_image,
        '--context', '/workspace',
        '--dockerfile', f'/workspace/{dockerfile}',
        '--destination', image_name,
        '--use-new-run',
        '--compressed-caching',
        '--single-snapshot',
        '--cleanup'
    ]
    
    for arg_name, arg_value in build_args.items():
        kaniko_command.extend(['--build-arg', f'{arg_name}={arg_value}'])
    
    logging.info(f"Building {service_name} with Kaniko: {' '.join(kaniko_command)}")
    
    result = subprocess.run(kaniko_command, capture_output=True, text=True)
    if result.returncode == 0:
        logging.info(f"Successfully built {service_name}")
        logging.info(result.stdout)
    else:
        logging.error(f"Error building {service_name}: {result.stderr}")

def main():
    setup_logging()
    
    compose_file = os.getenv('COMPOSE_FILE', 'docker-compose.yml')
    kaniko_image = os.getenv('KANIKO_IMAGE', 'gcr.io/kaniko-project/executor:latest')
    
    if not os.path.exists(compose_file):
        logging.error(f"{compose_file} not found")
        return
    
    compose_data = load_compose_file(compose_file)
    
    services = compose_data.get('services', {})
    image_names = defaultdict(int)
    
    for service_name, service_data in services.items():
        image_name = service_data.get('image')
        
        if not image_name:
            logging.warning(f"No image specified for service {service_name}")
            continue
        
        image_names[image_name] += 1
    
    for image_name, count in image_names.items():
        if count > 1:
            logging.error(f"Error: Image name {image_name} is used {count} times.")
            return
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for service_name, service_data in services.items():
            build_data = service_data.get('build', {})
            build_context = build_data.get('context', '.')
            dockerfile = build_data.get('dockerfile', 'Dockerfile')
            image_name = service_data.get('image')
            build_args = build_data.get('args', {})
            
            build_args = {key: os.getenv(key, value) for key, value in build_args.items()}
            
            if not image_name:
                logging.warning(f"No image specified for service {service_name}")
                continue
            
            futures.append(executor.submit(build_with_kaniko, service_name, build_context, dockerfile, image_name, build_args, kaniko_image))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                logging.error(f"Generated an exception: {exc}")

if __name__ == '__main__':
    main()
