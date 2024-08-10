# Changelog
* `1.1.0.0`:
    * Improvements, bugfixes
* `1.0.1.0`:
    * Fixed module naming. I am sorry.
    * Improvements, bugfixes
        * `--compose-file` - Path to docker-compose.yml file
        * `--kaniko-image` Kaniko executor image (def. `gcr.io/kaniko-project/executor:latest`)
        * `--push`, `--deploy`, `-d`, `-p` - Deploy the built images to the registry
        * `--dry-run`, `--dry` - Dry run: build images without pushing and with cleanup
        * `--version`, `-v` - Show script version
        * `--help`, `-h` - Show this help message and exit
* `0.0.1.1`:
    * Bugfixes
    * Updated args:
        * `--dry-run`, `--dry` - Dry run: build images without pushing and with cleanup
        * `--compose-file` - Path to `docker-compose.yml` file
        * `--kaniko-image` - Kaniko executor image (def. `gcr.io/kaniko-project/executor:latest`)
        * `--push`, `--deploy`, `-d`, `-p` -Deploy the built images to the registry
* `0.0.1.0`:
    * Bugfixes
    * Added support of "Dry Run" arg: `--dry`
* `0.0.0.9`:
    * Bugfixes
* `0.0.0.8`:
    * Added args support:
        * `--compose-file` - set path to compose file
        * `--kaniko-image` - set another version of kaniko image
        * `--deploy` - deploy afrer build
* `0.0.0.7`:
    * Added support of pushing new images to repository.
    * Added mounting credentails from host.
* `0.0.0.6`:
    * Added new default build arguments.
* `0.0.0.5`:
    * Bugfixes
    * The script will automatically use the variable values from .env for the build arguments, if specified, and pass them to the Kaniko command. If the build arguments are not specified, they simply will not be added to the command.
* `0.0.0.4`:
    * Added support of `.env` files. If file exists - script will be try to load ENVS.
* `0.0.0.3`:
    * Added support of parallel builds
* `0.0.0.2`:
    * Bugfixes
    * Added a check for the uniqueness of image names before starting the build and to prevent overwriting images with the same names and tags.
* `0.0.0.1`:
    * Bugfixes
    * Supported OS - Unix only. Because `kaniko` dont support `Windows`.
    * Added support of `image` tag from `docker-compose.yml`
* `0.0.0.0`:
    * First release