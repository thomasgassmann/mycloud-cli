# Swisscom myCloud CLI

Swisscom myCloud CLI is a command line utility to manage all your data stored on Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API.

# Installation

## Install via pip
To install or upgrade the myCloud CLI via pip, just run:
`python3 -m pip install --user --upgrade git+https://github.com/ThomasGassmann/mycloud-cli`

## Requirements
First install all dependencies:

`export PIPENV_VENV_IN_PROJECT="enabled"`
`pipenv install`

### Windows
mitmproxy is required to run this application on Windows. Install mitmproxy with the corresponding certificates in the Root CA.
To get the access token (when not passed manually), the proxy needs to run. To start the proxy run in directory `mycloud/mycloudapi`:

`mitmdump -p 8080 -s "proxy.py"`

Additonally `chromium` and `chromedriver` are required. Make sure both of them are in your `$PATH`.

# Run
To use the Swisscom myCloud CLI, run `mycloud [command]` in the root directory.

To get a list of all available commands, run:

`mycloud -h`

# FAQ
### How does myCloud CLI manage files stored on myCloud?
myCloud CLI adds an additional layer on top of the drive feature in myCloud. This allows it to keep track of file versions and save metadata for these files when uploading them.
Each file being processed by myCloud CLI is stored within a folder matching its upload path. Within this folder, myCloud CLI will save a `mycloud_metadata.json` file and a folder for each version. The metadata file contains references to the files and metadata of the files.




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
