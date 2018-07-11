from mycloudapi import MyCloudRequestExecutor, PutObjectRequest, GetObjectRequest, MetadataRequest
from flask import Flask, request, Response
from constants import ENCRYPTION_CHUNK_LENGTH
from logger import log


def run_server(request_executor: MyCloudRequestExecutor, mycloud_base_dir: str, port: int):
    app = Flask(__name__)


    def _up_generator(stream):
        while True:
            cur_data = stream.read(ENCRYPTION_CHUNK_LENGTH)
            if cur_data is None or len(cur_data) != ENCRYPTION_CHUNK_LENGTH:
                yield cur_data if cur_data is not None else bytes([])
                break
            yield cur_data


    def _build_object_resource(path: str):
        nonlocal mycloud_base_dir
        if path.startswith('/'):
            path = path[1:]
        if not mycloud_base_dir.endswith('/'):
            mycloud_base_dir += '/'
        return mycloud_base_dir + path


    @app.route('/', defaults={'path': ''}, methods=['POST', 'GET'])
    @app.route('/<path:path>', methods=['POST', 'GET'])
    def mycloud(path: str):
        object_resource = _build_object_resource(path)
        if request.method == 'GET':
            return download(object_resource)
        elif request.method == 'POST':
            return upload(object_resource)
        else:
            return 'Invalid HTTP verb', 400


    def upload(object_resource: str):
        if len(request.files) != 1:
            return 'Request must contain 1 file', 400
        
        log(f'Uploading file to {object_resource}...')
        file_key = [key for key in request.files.keys()][0]
        file = request.files[file_key]
        generator = _up_generator(file)
        put_request = PutObjectRequest(object_resource, generator)
        response = request_executor.execute_request(put_request)
        if response.status_code == 200:
            return 'Upload successful', 200
        else:
            return 'Upload failed', 400


    def download(object_resource: str):
        log(f'Downloading file {object_resource}...')
        get_request = GetObjectRequest(object_resource, ignore_bad_request=True, ignore_not_found=True)
        response = request_executor.execute_request(get_request)
        if response.status_code != 200:
            # return try_return_directory(object_resource)
            return 'Invalid path', 400

        def _generator():
            for chunk in response.iter_content(chunk_size=ENCRYPTION_CHUNK_LENGTH):
                yield chunk
        return Response(_generator(), 200, mimetype='application/octet-stream')


    def try_return_directory(object_resource: str):
        request = MetadataRequest(object_resource, ignore_not_found=True)
        response = request_executor.execute_request(request)
        if response.status_code != 200:
            return 'Invalid path', 400
        
        return Response(response.text, 200, mimetype='application/json')

    
    app.run(port=port)
    log(f'Successfully started local proxy on port {str(port)}...')