from mycloudapi import MyCloudRequestExecutor
import flask


class ProxyServer:
    def __init__(self, request_executor: MyCloudRequestExecutor, mycloud_base_dir: str):
        self.request_executor = request_executor
        self.mycloud_base_dir = mycloud_base_dir


    def run_server(self):
        pass