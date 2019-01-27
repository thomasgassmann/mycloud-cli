# Swisscom myCloud CLI

Swisscom myCloud CLI is a command line utility to manage all your data stored on Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API.

# Installation

First, make sure `chromium` and `chromedriver` are installed and in  your `$PATH`.

To install or upgrade myCloud CLI via pip, run:
```
python3 -m pip install --user --upgrade git+https://github.com/ThomasGassmann/mycloud-cli
```

After installing myCloud CLI make sure to add the certificates for mitmproxy to your CA in your OS / Chromium. Run:
```
mycloud cert
```

to download the required certificate. 
To use myCloud CLI, run `mycloud [command]`.
To get a list of all available commands, run:
```
mycloud -h
```

# Setup local environment
First, clone the repository:
```
git clone https://github.com/thomasgassmann/mycloud-cli`
```

Then install all dependencies via pipenv:
```
cd mycloud-cli
export PIPENV_VENV_IN_PROJECT="enabled"
pipenv install
pipenv shell
```
Then run `python -m mycloud cert` to install the certificates as described in the [Installation](#Installation) section.
