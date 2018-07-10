from mycloudapi import MyCloudRequestExecutor, PutObjectRequest
from flask import Flask, request
from constants import ENCRYPTION_CHUNK_LENGTH
from logger import log


app = Flask(__name__)


class ProxyServer:
    def __init__(self, request_executor: MyCloudRequestExecutor, mycloud_base_dir: str, port: int):
        ProxyServer.request_executor = request_executor
        ProxyServer.mycloud_base_dir = mycloud_base_dir
        ProxyServer.port = port


    def run_server(self):
        app.run(port=self.port)
        log(f'Successfully started local proxy on port {str(self.port)}...')

    
    @app.route('/<path>', methods=['POST'])
    def upload(path: str):
        if len(request.files) != 1:
            return str(400), 'Request must contain 1 file'
        
        object_resource = ProxyServer._build_object_resource(path)
        log(f'Uploading file to {object_resource}...')
        file_key = [key for key in request.files.keys()][0]
        file = request.files[file_key]
        generator = ProxyServer._up_generator(file)
        put_request = PutObjectRequest(object_resource, generator)
        response = ProxyServer.request_executor.execute_request(put_request)
        return str(200), '?'


    @app.route('/<path>', methods=['GET'])
    def download(path: str):
        pass


    @staticmethod
    def _up_generator(stream):
        while True:
            cur_data = stream.read(ENCRYPTION_CHUNK_LENGTH)
            if cur_data is None or len(cur_data) != ENCRYPTION_CHUNK_LENGTH:
                yield cur_data if cur_data is not None else bytes([])
                break
            yield cur_data


    @staticmethod
    def _build_object_resource(path: str):
        if path.startswith('/'):
            path = path[1:]
        if not ProxyServer.mycloud_base_dir.endswith('/'):
            ProxyServer.mycloud_base_dir += '/'
        return ProxyServer.mycloud_base_dir + path