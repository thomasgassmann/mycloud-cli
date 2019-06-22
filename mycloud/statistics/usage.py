import click
from tabulate import tabulate
from mycloud.mycloudapi import MyCloudRequestExecutor, UsageRequest


def print_usage(request_executor: MyCloudRequestExecutor):
    request = UsageRequest()
    response = request_executor.execute_request(request)
    formatted = UsageRequest.format_response(response)
    data = []
    for item in formatted:
        data.append([
            item,
            formatted[item]
        ])

    click.echo(tabulate(data, ['Name', 'Value'], tablefmt='fancy_grid'))
