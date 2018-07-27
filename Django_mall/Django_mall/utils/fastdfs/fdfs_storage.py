from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    def __init__(self, client_conf=None, base_url=None):
        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_BASE_URL


    def _open(self, name, mode='rb'):
        pass

    def _save(self,name,content):
        # client = Fdfs_client('Django_mall/utils/fastdfs/client.conf')
        client = Fdfs_client(self.client_conf)

        # ret = client.upload_by_filename('/home/python/Desktop/1832281101296aa049d1ly1fnvfanfttdj20rs15o4qp.jpg')
        ret = client.upload_by_buffer(content.read())
        if ret.get('Status') != 'Upload successed.':
            raise Exception('fdfs upload error')
        file_id = ret.get('Remote file_id')
        return file_id

    def exists(self, name):
        return False

    def url(self, name):
        return self.base_url+name


