# [![Activity](https://img.shields.io/github/commit-activity/m/EpicMorg/kaniko-wrapper?label=commits&style=flat-square)](https://github.com/EpicMorg/kaniko-wrapper/commits) [![GitHub issues](https://img.shields.io/github/issues/EpicMorg/kaniko-wrapper.svg?style=popout-square)](https://github.com/EpicMorg/kaniko-wrapper/issues) [![GitHub forks](https://img.shields.io/github/forks/EpicMorg/kaniko-wrapper.svg?style=popout-square)](https://github.com/EpicMorg/kaniko-wrapper/network) [![GitHub stars](https://img.shields.io/github/stars/EpicMorg/kaniko-wrapper.svg?style=popout-square)](https://github.com/EpicMorg/kaniko-wrapper/stargazers)  [![Size](https://img.shields.io/github/repo-size/EpicMorg/kaniko-wrapper?label=size&style=flat-square)](https://github.com/EpicMorg/kaniko-wrapper/archive/master.zip) [![Release](https://img.shields.io/github/v/release/EpicMorg/kaniko-wrapper?style=flat-square)](https://github.com/EpicMorg/kaniko-wrapper/releases) [![GitHub license](https://img.shields.io/github/license/EpicMorg/kaniko-wrapper.svg?style=popout-square)](LICENSE.md) [![Changelog](https://img.shields.io/badge/Changelog-yellow.svg?style=popout-square)](CHANGELOG.md) [![PyPI - Downloads](https://img.shields.io/pypi/dm/kaniko-wrapper?style=flat-square)](https://pypi.org/project/kaniko-wrapper/)

## Description
Python wrapper for run kaniko from shell with parameters from `docker-compose.yml` file.

## Motivation
1. You have Docker project thar contains:
1.1 `docker-compose.yml` - as build manifest
1.2 One or more `Dockerfile`s in project
2. You want to automate builds with `kaniko` build system.
3. `kaniko` dont support `docker-compose.yml` builds.

## How to

> **Requerments** Minimal `Python` version is `3.9`. 

```
pip install kaniko-wrapper
cd <...>/directory/contains/docker/and/docker-compose-file/
kaniko-wrapper
```

> **Note on the executor image.** Google archived the original `kaniko` in 2025
> and `gcr.io/kaniko-project/executor` is frozen at `v1.24.0`. The default
> executor is now the community fork `ghcr.io/osscontainertools/kaniko:latest`.
> Pin a tag in CI and override with `--kaniko-image` / `KANIKO_IMAGE` if needed.

### Arguments (examples)
* `--compose-file` - Path to docker-compose.yml file
* `--kaniko-image` - Kaniko executor image (def. `ghcr.io/osscontainertools/kaniko:latest`)
* `--push`, `--deploy`, `-d`, `-p` - Build and push to the registry and all `x-mirrors`
* `--dry-run`, `--dry` - Dry run: build images without pushing
* `--no-push` - Build without pushing to the registry
* `--verbose`, `-V` - Verbose output (shortcut for `--log-level DEBUG`)
* `--log-level` - Override log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
* `--engine` - Container engine: `docker` (default) or `podman`
* `--network NET` - Executor run network (e.g. host); default host for podman
* `--squash / --no-squash` - Single-layer output, default on (x-squash overrides per service)
* `--version`, `-v` - Show script version
* `--help`, `-h` - Show this help message and exit

 

## Supported features (example):

1. Single project in `docker-compose.yml`
```
services:
  app:
    image: "EpicMorg/kaniko-wrapper:image"
    build:
      context: .
      dockerfile: ./Dockerfile
```

2. Multiproject in `docker-compose.yml`

```
services:
  app:
    image: "EpicMorg/kaniko-wrapper:image-jdk11"
    build:
      context: .
  app-develop:
    image: "EpicMorg/kaniko-wrapper:image-develop-jdk11"
    build:
      context: .
      dockerfile: ./Dockerfile.develop
      x-squash: false
  app-develop-17:
    image: "epicmorg/astralinux:image-develop-jdk17"
    build:
      context: .
      dockerfile: ./Dockerfile.develop-17
      x-squash: true
```

3. Mirrors — push one build to several registries

Add an `x-mirrors` list to a service. On `--push`, the built image is pushed to
the primary `image` and to every mirror in a single build (multiple
`--destination`). A failed push to any mirror fails the build. All target
registries must be authenticated in `~/.docker/config.json`.

```
services:
  app:
    image: docker.io/epicmorg/app:latest
    build:
      context: .
    x-mirrors:
      - quay.io/epicmorg/app:latest
      - my.owned.hub/epicmorg/app:latest
```

4. Squash (`docker-compose.yml`):
  Add an `x-squash` field to a compose service to control single-layer output. Default is true (squash on).

```
  services:
    app:
      image: docker.io/epicmorg/app:latest
      x-squash: false
``` 
