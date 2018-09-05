# Swisscom myCloud Backup

Swisscom myCloud Backup is a backup solution, which is supposed to backup all files on your computer to Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API. Additionally the script can encrypt the files it backs up. 
Files larger than approx. 3GB are not allowed by Swisscom. Therefore this backup tool automatically chunks files larger than 3GB into smaller files. The threshold values can be adjusted in `constants.py`.

## Requirements
First install all dependencies:
`python -m pip install -r requirements.txt`

mitmproxy is required to run this application. Install mitmproxy with the corresponding certificates in the Root CA. 
To get the access token (when not passed manually), the proxy needs to run. To start the proxy run in directory `mycloud/mycloudapi`:
`mitmdump -p 8080 -s "proxy.py"`

Additonally Chromium and the corresponding web driver is required:
`sudo apt-get install chromium chromium-driver`

## Todos
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
- [ ] Machine Learning to prioritize files to upload
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
