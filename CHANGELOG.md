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