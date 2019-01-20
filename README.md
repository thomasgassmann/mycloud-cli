# Swisscom myCloud CLI

Swisscom myCloud CLI is a command line utility to manage all your data stored on Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API.

# Installation

First, make sure `chromium` and `chromedriver` installed and in  your `$PATH`.

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



# Todos (migrate to Github Issues)
- [ ] Consider replacements.json on download
- [ ] Use scandir instead of os.walk
- [ ] Only store hashed password in memory
- [ ] Automatically launch proxy and close it, when needed
- [ ] Custom WebDAV proxy with support for Synology Cloud Sync
- [ ] In case of KeyboardInterrupt: join all running threads. handle keyboardInterrupt properly in other threads
- [ ] Rename multiple requests in one file
- [ ] Use multiple network interfaces to send requests (for example WiFi and 4G)
- [ ] Faster check if file was already uploaded: Hashing for local files? Update date for bigger ones?
- [ ] Do things in parallel (especially hashing)
- [ ] Replace argparse with fire
- [ ] Loop faster through files locally
- [ ] Improve upload and statistics speed
- [ ] Statistics: List all files with certain extension
- [ ] Delete all files with specified extension
- [ ] Delete all unencrypted files
- [ ] Watch command: Watch file system and sync
- [ ] Update proxy mode
- [ ] Improve TCP performance
- [ ] Machine Learning to prioritize files to upload (learn to ignore node_modules, weird exes and things under program files)
- [ ] Request caching

## General Notes on API (TDB)

ZIP DOWNLOAD:
POST: https://storage.prod.mdl.swisscom.ch/jobs/zip

MOVE TRASH:
PUT: https://storage.prod.mdl.swisscom.ch/trash/items

GET MAX FILE SIZE:
POST https://storage.prod.mdl.swisscom.ch/lfs

PARTIAL UPLOAD FOR FILE (still max 3 GB?)
POST https://storage.prod.mdl.swisscom.ch/lfs/[id]/[partIndex]
where id returned from previous endpoint

SESSIONS:
GET https://identity.prod.mdl.swisscom.ch/sessions?nocache=1532216378144

CONFIG
GET https://swisscom.zendesk.com/embeddable/config

ME
GET https://identity.prod.mdl.swisscom.ch/me

MOVE
https://storage.prod.mdl.swisscom.ch/commands/move
not sure whether this is any different than rename?
