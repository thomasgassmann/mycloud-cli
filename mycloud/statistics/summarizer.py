import click
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.logger import log


def summarize(reuqest_executor: MyCloudRequestExecutor, mycloud_dir: str):
    click.echo('Summarizing directory {}...'.format(mycloud_dir))
