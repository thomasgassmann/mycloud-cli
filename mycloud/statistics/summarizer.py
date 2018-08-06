from mycloudapi import MyCloudRequestExecutor
from logger import log


def summarize(reuqest_executor: MyCloudRequestExecutor, mycloud_dir: str):
    log(f'Summarizing directory {mycloud_dir}...')