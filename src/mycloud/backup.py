import argparse, os, sys
from upload import Uploader
from download import download
from mycloudapi import get_bearer_token, ObjectResourceBuilder
from progress import ProgressTracker, LazyCloudProgressTracker, FileProgressTracker, CloudProgressTracker


parser = argparse.ArgumentParser(description='Swisscom myCloud Backup')
parser.add_argument('--direction', metavar='i', type=str, help='The direction of the backup (1 = up, 0 = down')
parser.add_argument('--local_dir', metavar='d', type=str, help='The directory to backup')
parser.add_argument('--mycloud_dir', metavar='m', type=str, help='Base path in my cloud to upload to (must start with /Drive/)')
parser.add_argument('--progress_type', metavar='v', type=str, help='Progress type (CLOUD: Use files in cloud, LAZY_CLOUD: Use files in cloud lazily, FILE: Use local file, progress_file parameter required')
parser.add_argument('--progress_file', metavar='p', type=str, help='Save progress file name')
parser.add_argument('--encryption_pwd', metavar='e', type=str, help='Encryption Password')
parser.add_argument('--token', metavar='t', type=str, help='Pass token manually')
parser.add_argument('--skip', metavar='s', help='Paths to skip', nargs='+')

args = parser.parse_args()

if args.progress_type is None or not (args.direction == '1' or args.direction == '0') or args.local_dir is None or args.direction is None or args.mycloud_dir is None or not args.mycloud_dir.startswith('/Drive/'):
    parser.print_help()
    sys.exit(1)

bearer = get_bearer_token() if args.token is None else args.token
is_encrypted = args.encryption_pwd is not None

if args.progress_type == 'CLOUD' and args.direction == '1':
    tracker = CloudProgressTracker(bearer, args.mycloud_dir)
elif args.progress_type == 'LAZY_CLOUD' and args.direction == '1':
    tracker = LazyCloudProgressTracker(bearer)
elif args.progress_file is not None and args.progress_type == 'FILE':
    tracker = FileProgressTracker(args.progress_file)
else:
    parser.print_help()
    sys.exit(1)

tracker.load_if_exists()
if args.skip is not None:
    skipped = ', '.join(args.skip)
    print(f'Skipping files: {skipped}')
    tracker.set_skipped_paths(args.skip)

builder = ObjectResourceBuilder(args.local_dir, args.mycloud_dir, is_encrypted)

if args.direction == '1':
    uploader = Uploader(bearer, args.local_dir, args.mycloud_dir, tracker, args.encryption_pwd)
    uploader.upload()
elif args.direction == '0':
    download(bearer, args.local_dir, args.mycloud_dir, tracker, is_encrypted, args.encryption_pwd)