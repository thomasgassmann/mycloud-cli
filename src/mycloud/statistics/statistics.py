from mycloudapi import ObjectResourceBuilder


class Statistics:
    def __init__(self, mycloud_dir: str, token: str):
        self.mycloud_dir = mycloud_dir
        self.token = token