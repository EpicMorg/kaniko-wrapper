import os
import yaml
import subprocess

def load_compose_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def build_with_kaniko(service_name, build_context, dockerfile, image_name, tag):
    kaniko_command = [
        'docker', 'run',
        '--rm',
        '-v', f'{os.path.abspath(build_context)}:/workspace',
        'gcr.io/kaniko-project/executor:latest',
        '--context', '/workspace',
        '--dockerfile', f'/workspace/{dockerfile}',
        '--destination', f'{image_name}:{tag}'
    ]
    
    print(f"Building {service_name} with Kaniko: {' '.join(kaniko_command)}")
    
    result = subprocess.run(kaniko_command, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Successfully built {service_name}")
    else:
        print(f"Error building {service_name}: {result.stderr}")

def main():
    compose_file = 'docker-compose.yml'
    
    if not os.path.exists(compose_file):
        print(f"{compose_file} not found")
        return
    
    compose_data = load_compose_file(compose_file)
    
    services = compose_data.get('services', {})
    for service_name, service_data in services.items():
        build_data = service_data.get('build', {})
        build_context = build_data.get('context', '.')
        dockerfile = build_data.get('dockerfile', 'Dockerfile')
        image_name = service_data.get('image', f"{service_name}-image")
        tag = 'latest'
        
        build_with_kaniko(service_name, build_context, dockerfile, image_name, tag)

if __name__ == '__main__':
    main()
