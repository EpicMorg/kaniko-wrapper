# EpicMorg: Kaniko-Compose Wrapper

## Description

This script is designed to automate Docker image building using **Kaniko** and **docker-compose**. It supports testing, deployment, and publishing images to a registry.

## Usage

```bash
kaniko [options...] <command> [<args>...]
kaniko (-h | --help | --version)
```

#### Global Options:
`-e, --allow-dotenv <path>`
Load environment variables from the specified file.
[default: .env]

`-h, --help` - Show usage help.

`--version` - Show the script version.

#### Commands:

`build` - Run image building with Kaniko.

#### Examples:
1. Build and push images with default settings:
```bash
kaniko build --push
```
This will use the default docker-compose.yml and the Kaniko image gcr.io/kaniko-project/executor:latest. The built images will be pushed to the registry.

2. Build using a custom docker-compose file and Kaniko image:
```bash
kaniko build --compose-file=custom-compose.yml --kaniko-image=my-kaniko-image
```
This command allows you to specify a custom docker-compose file and a Kaniko image for the build.

3. Test build without pushing to the registry (Dry-run):
```bash
kaniko build --dry-run
```
This will run the build process without pushing the images to the registry. It is useful for testing the build process.

#### Configuration
```bash
.env file
```
You can specify environment variables for your builds via a .env file. If the --allow-dotenv option is used, the script will automatically load environment variables from this file.

Example .env file: `MY_VAR=value`

To use a custom dotenv file:

```bash
kaniko build --allow-dotenv custom.env
```
#### Error Handling

1. Invalid command
If you provide an unknown command, the script will raise an error:

```bash
Unknown command: <command>
```

2. Missing docker-compose file
If the `--compose-file` option is not provided and the file cannot be found, the script will display an error:

```bash
Error: <file> not found
```
3. Kaniko image missing
If the `--kaniko-image` option is missing or invalid, an error message will be shown:

```bash
Error: Kaniko image is missing. Please provide a valid image with --kaniko-image.
```

#### Version Management
The version of the script can be checked using the --version option:

```bash
kaniko --version
```
This will print the version of the script, for example: `Kaniko Builder Version: 1.1.0.0`