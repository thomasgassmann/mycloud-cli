# Swisscom myCloud Backup

Swisscom myCloud Backup is a backup solution, which is supposed to backup all files on your computer to Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API. Additionally the script can encrypt the files it backs up. 
Files larger than approx. 3GB are not allowed by Swisscom. Therefore this backup tool automatically chunks files larger than 3GB into smaller files. The threshold values can be adjusted in `constants.py`.

## Requirements
mitmproxy is required to run this application. Install mitmproxy with the corresponding certificates in the Root CA. 
To get the access token (when not passed manually), the proxy needs to run. To start the proxy run in directory `mycloud/mycloudapi`:
`mitmdump -p 8080 -s "proxy.py"`

## Todos
- [ ] Use multiple network interfaces to send requests (for example WiFi and 4G)
- [ ] Faster check if file was already uploaded: Hashing for local files? Update date for bigger ones?
- [ ] Do things in parallel (especially hashing)
- [ ] Replace argparse with fire
- [ ] Auto-Setup command
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
