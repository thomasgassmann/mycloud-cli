from mycloudapi import MyCloudRequestExecutor, UsageRequest
from logger import log
from tabulate import tabulate


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

    print(tabulate(data, ['Name', 'Value'], tablefmt='fancy_grid'))