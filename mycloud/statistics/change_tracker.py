from tabulate import tabulate
from mycloud.mycloudapi import MyCloudRequestExecutor, ChangeRequest


def track_changes(request_executor: MyCloudRequestExecutor, mycloud_dir: str, top: int):
    change_request = ChangeRequest(mycloud_dir, top)
    response = request_executor.execute_request(change_request)
    items = ChangeRequest.format_response(response)
    data = []
    for item in items:
        data.append([
            item['Name'],
            item['CreationTime'],
            item['ModificationTime'],
            item['Length']
        ])

    print(tabulate(data, ['Name', 'Creation Time',
                          'Modification Time', 'Length'], tablefmt='fancy_grid'))
