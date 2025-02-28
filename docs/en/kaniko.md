## What is Kaniko?

There are a few steps to working with Kaniko and automating the process of building Docker images using Kaniko with or without Docker Compose.

`Kaniko` is a tool for building Docker images in Kubernetes or other containerized environments. Kaniko runs in a container and does not require Docker Daemon on the machine, making it useful for working in CI/CD processes or in containerized environments.

## How to get started with Kaniko

Installing Kaniko

If you want to use Kaniko locally (on your machine), you need to install Docker and Docker Compose first.
- Install Docker:
- Install Docker Compose:

After that, you can start using Kaniko. For local work, you can run it in a container using the Docker command.

Using Docker Compose with Kaniko: If you use Docker Compose to build multiple services, Kaniko can work with docker-compose.yml files.

#### Requirements:
- You must have a Dockerfile.
- You need to authenticate to the registry (e.g. Docker Hub or Google Container Registry).
- Make sure you have permissions to push to the specified repository.

#### Recommendations

- Make sure you have a properly configured Dockerfile and that all dependencies inside your project are specified correctly.

- For private registries (e.g. Docker Hub or GCR), you must authenticate with Docker:

```bash
docker login
```
This will allow Kaniko to access your registry.

- For Google Container Registry, you need to set up authentication with a service account file or the gcloud auth configure-docker command.

#### Full example with Kaniko

- Create a project with a Dockerfile and docker-compose.yml.

- Make sure you have access to the registry (e.g. Docker Hub or Google Container Registry).

- Run the build with Kaniko with the correct paths and parameters.

```bash
kaniko-wrapper --dry-run
```

#### Key points:
- `--compose-file` specifies the path to Docker Compose or to the folder with the Dockerfile.

- `--kaniko-image` specifies the Kaniko image that will be used for the build.

- `--push` means that after the build, the images will be uploaded to the registry.

- `--destination` specifies where to send the built images (e.g. Docker Hub or Google Container Registry).

And if you run with kaniko_wrapper - everything will be much shorter:

First, you need to go to the folder with Docker (see the example in the project in the docker folder, how this can be arranged).
` cd /home/./././docker`
```bash
kaniko-wrapper --push
```