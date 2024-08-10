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
```
pip install kaniko-wapper
cd <...>/directory/contains/docker/and/docker-compose-file/
kaniko-wapper
```

### Arguments (examples)
* `--compose-file` - Path to docker-compose.yml file
* `--kaniko-image` Kaniko executor image (def. `gcr.io/kaniko-project/executor:latest`)
* `--push`, `--deploy`, `-d`, `-p` - Deploy the built images to the registry
* `--dry-run`, `--dry` - Dry run: build images without pushing and with cleanup
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
  app-develop-17:
    image: "epicmorg/astralinux:image-develop-jdk17"
    build:
      context: .
      dockerfile: ./Dockerfile.develop-17
```
