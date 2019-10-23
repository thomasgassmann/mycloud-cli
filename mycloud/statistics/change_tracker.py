import click
from tabulate import tabulate
from mycloud.mycloudapi import MyCloudRequestExecutor, ObjectResourceBuilder
from mycloud.mycloudapi.requests.drive import ChangeRequest


async def track_changes(request_executor: MyCloudRequestExecutor, mycloud_dir: str, top: int):
    mycloud_dir = ObjectResourceBuilder.correct_suffix_sep(
        mycloud_dir, is_file=False)
    change_request = ChangeRequest(mycloud_dir, top)
    response = await request_executor.execute_request(change_request)
    items = ChangeRequest.format_response(response)
    data = []
    for item in items:
        data.append([
            item['Name'],
            item['CreationTime'],
            item['ModificationTime'],
            item['Length']
        ])

    click.echo(tabulate(data, ['Name', 'Creation Time',
                               'Modification Time', 'Length'], tablefmt='fancy_grid'))
