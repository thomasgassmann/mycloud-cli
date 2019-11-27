# Swisscom myCloud CLI

![](https://github.com/thomasgassmann/mycloud-cli/workflows/.github/workflows/ci.yml/badge.svg)

Swisscom myCloud CLI is a command line utility to manage all your data stored on Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API.

# Requirements
[Gnome Keyring](https://wiki.gnome.org/Projects/GnomeKeyring) is required in order to store the the credentials for myCloud.

# Installation

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
To use myCloud CLI, run `mycloud [command]`.
Then authenticate yourself with your username and password using:

```
mycloud auth login
```

To get a list of all available commands, run:

```
mycloud -h
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
pipenv install --python 3.6
pipenv shell
```

Then run `python -m mycloud auth cert` to install the certificates as described in the [Installation](#Installation) section.
