# Swisscom myCloud CLI

![](https://github.com/thomasgassmann/mycloud-cli/workflows/.github/workflows/release.yml/badge.svg)

> THIS PROJECT IS NO LONGER ACTIVELY MAINTAINED

Swisscom myCloud CLI is a command line utility to manage all your data stored on Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API.

# Requirements
Any Keyring Backend comptatible with the [keyring](https://pypi.org/project/keyring) package is required in order to store the credentials for myCloud.

# Usage

## Docker

```
docker run -it mycloud-cli
```

## Manual Installation

First, make sure `chromium` and `chromedriver` are installed and in your `$PATH`.

To install or upgrade myCloud CLI via pip, run:

```
python3 -m pip install --user --upgrade mycloud-cli
```

After installing myCloud CLI make sure to add the certificates for mitmproxy to your CA in your OS / Chromium. Run:

```
mycloud auth cert
```

to download the required certificate.

## Authenticate
To use myCloud CLI, run `mycloud [command]`.
Then authenticate yourself with your username and password using:

```
mycloud auth login
```

To get a list of all available commands, run:

```
mycloud -h
```

## WebDAV

myCloud CLI includes a basic WebDAV Proxy out of the box.

To run it, first configure the credentials for the WebDAV server using:

```bash
mycloud config webdav
```

Then start the server using:

```bash
mycloud webdav --host ip --port port
```

# Setup local environment

First, clone the repository:

```
git clone https://github.com/thomasgassmann/mycloud-cli
```

Then install all dependencies via pipenv:

```
cd mycloud-cli
export PIPENV_VENV_IN_PROJECT="enabled"
pipenv install --python 3.7
pipenv shell
```

Then run `python -m mycloud auth cert` to install the certificates as described in the [Installation](#Installation) section.
