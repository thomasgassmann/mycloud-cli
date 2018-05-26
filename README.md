# Swisscom myCloud Backup

Swisscom myCloud Backup is a backup solution, which is supposed to backup all files on your computer to Swisscom myCloud. To achieve this, it uses the public Swisscom myCloud API. Additionally the script can encrypt the files it backs up. 
Files larger than approx. 3GB are not allowed by Swisscom. Therefore this backup tool automatically chunks files larger than 3GB into smaller files. The threshold values can be adjusted in `constants.py`.

## So how do I back something up?
Navigate to `src/mycloud` directory.

`python backup.py --token MY_TOKEN --local_dir LOCAL_PATH --mycloud_dir /Drive/LOCAL_PATH/ --encryption_pwd MY_SUPER_SECRET_PASSWORD --direction 1 --skip C:\$RECYCLE.BIN --progress_type LAZY_CLOUD_CACHE --progress_file C:\progress.json`

## And how would I download these files again?
Navigate to `src/mycloud` directory.

`python backup.py --token MY_TOKEN --local_dir LOCAL_PATH --mycloud_dir /Drive/LOCAL_PATH/ --encryption_pwd MY_SUPER_SECRET_PASSWORD --direction 0 -progress_type FILE --progress_file C:\progress.json`

## Need more help?
1. Run `python backup.py -h`
2. Google
3. Contact developer
