import argparse, os, sys
from uploader import upload
from mycloudapi.bearer_token import get_bearer_token
from downloader import download
from progress_tracker import ProgressTracker


parser = argparse.ArgumentParser(description='Swisscom myCloud Backup')
parser.add_argument('--direction', metavar='i', type=str, help='The direction of the backup (1 = up, 0 = down')
parser.add_argument('--local_dir', metavar='d', type=str, help='The directory to backup')
parser.add_argument('--mycloud_dir', metavar='m', type=str, help='Base path in my cloud to upload to (must start with /Drive/)')
parser.add_argument('--progress_file', metavar='p', type=str, help='Save progress file name')
parser.add_argument('--encryption_pwd', metavar='e', type=str, help='Encryption Password')
parser.add_argument('--token', metavar='t', type=str, help='Pass token manually')
parser.add_argument('--batch_size', metavar='t', type=int, help='Batch size (not available for download, yet)')
parser.add_argument('--skip', metavar='s', help='Paths to skip', nargs='+')

args = parser.parse_args()	

if not (args.direction is '1' or args.direction is '0') or args.local_dir is None or args.direction is None or args.mycloud_dir is None or not args.mycloud_dir.startswith('/Drive/') or args.progress_file is None:
    parser.print_help()
    sys.exit(1)

batch = args.batch_size if args.batch_size is not None else 1
bearer = get_bearer_token() if args.token is None else args.token
is_encrypted = args.encryption_pwd is not None

tracker = ProgressTracker(args.progress_file)
tracker.load_if_exists()
if args.skip is not None:
    skipped = ', '.join(args.skip)
    print(f'Skipping files: {skipped}')
    tracker.set_skipped_paths(args.skip)

if args.direction is '1':
    upload(batch, bearer, args.local_dir, args.mycloud_dir, tracker, is_encrypted, args.encryption_pwd)
elif args.direction is '0':
    download(bearer, args.local_dir, args.mycloud_dir, tracker, is_encrypted, args.encryption_pwd)