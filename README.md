# kaniko-wrapper
Python wrapper for run kaniko from shell with parameters from `docker-compose.yml` file.

## Motivation
1. You have Docker project thar contains:
1.1 `docker-compose.yml` - as build manifest
1.2 One or more `Dockerfile`s in project
2. You want to automate builds with `kaniko` build system.
3. `kaniko` dont support `docker-compose.yml` builds.

## How to
```
pip install kaniko-wapper
cd <...>/directory/contains/docker/and/docker-compose-file/
kaniko-wapper
```

### Arguments
* `--compose-file` - set path to compose file;
* `--kaniko-image` - set another version of kaniko image;
* `--deploy` - deploy afrer build;

## Supported features (example):

1. Single project in `docker-compose.yml`
```
services:
  app:
    image: "epicmorg/docker:image"
    build:
      context: .
      dockerfile: ./Dockerfile
```

2. Multiproject in `docker-compose.yml`

```
services:
  app:
    image: "epicmorg/docker:image-jdk11"
    build:
      context: .
  app-develop:
    image: "epicmorg/docker:image-develop-jdk11"
    build:
      context: .
      dockerfile: ./Dockerfile.develop
  app-develop-17:
    image: "epicmorg/astralinux:image-develop-jdk17"
    build:
      context: .
      dockerfile: ./Dockerfile.develop-17
```
