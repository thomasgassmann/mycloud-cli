import click
from mycloud.mycloudapi import MyCloudRequestExecutor


def summarize(reuqest_executor: MyCloudRequestExecutor, mycloud_dir: str):
    click.echo('Summarizing directory {}...'.format(mycloud_dir))
