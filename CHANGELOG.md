# Changelog
* `0.0.0.0`:
    * First release
* `0.0.0.1`:
    * Bugfixes
    * Supported OS - Unix only. Because `kaniko` dont support `Windows`.
    * Added support of `image` tag from `docker-compose.yml`
* `0.0.0.2`:
    * Bugfixes
    * Added a check for the uniqueness of image names before starting the build and to prevent overwriting images with the same names and tags.
* `0.0.0.3`:
    * Added support of parallel builds
* `0.0.0.4`:
    * Added support of `.env` files. If file exists - script will be try to load ENVS.
* `0.0.0.5`:
    * Bugfixes
    * The script will automatically use the variable values from .env for the build arguments, if specified, and pass them to the Kaniko command. If the build arguments are not specified, they simply will not be added to the command.
* `0.0.0.6`:
    * Added new default build arguments.
* `0.0.0.7`:
    * Added support of pushing new images to repository.
    * Added mounting credentails from host.
