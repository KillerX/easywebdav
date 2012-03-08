import requests
import shutil
from numbers import Number
from httplib import responses as HTTP_CODES

class WebdavException(Exception):
    pass

class ConnectionFailed(WebdavException):
    pass

class OperationFailed(WebdavException):
    _OPERATIONS = dict(
        GET = "download",
        PUT = "upload",
        DELETE = "delete",
        MKCOL = "create directory",
        )
    def __init__(self, method, path, expected_code, actual_code):
        self.method = method
        self.path = path
        self.expected_code = expected_code
        self.actual_code = actual_code
        operation_name = self._OPERATIONS[method]
        self.reason = 'Failed to {operation_name} "{path}"'.format(**locals())
        expected_code_str, actual_code_str = HTTP_CODES[expected_code], HTTP_CODES[actual_code]
        msg = '''\
{self.reason}.
  Operation     :  {method} {path}
  Expected code :  {expected_code} {expected_code_str}
  Actual code   :  {actual_code} {actual_code_str}'''.format(**locals())
        super(OperationFailed, self).__init__(msg)

class Client(object):
    def __init__(self, host, port=80, username=None, password=None):
        self.baseurl = 'http://{}:{}'.format(host ,port)
        self.cwd = '/'
        self.session = requests.session()
        if username and password:
            self.session.auth = (username, password)
    def _send(self, method, path, expected_code, **kwargs):
        url = self._get_url(path)
        response = self.session.request(method, url, **kwargs)
        if isinstance(expected_code, Number) and response.status_code != expected_code \
            or not isinstance(expected_code, Number) and response.status_code not in expected_code:
            raise OperationFailed(method, path, expected_code, response.status_code)
        return response
    def _get_url(self, path):
        path = str(path).strip()
        if path.startswith('/'):
            return self.baseurl + path
        return "".join((self.baseurl, self.cwd, path))
    def cd(self, path):
        path = path.strip()
        if not path:
            return
        stripped_path = '/'.join(part for part in path.split('/') if part) + '/'
        if stripped_path == '/':
            self.cwd = stripped_path
        elif path.startswith('/'):
            self.cwd = '/' + stripped_path
        else:
            self.cwd += stripped_path
    def mkdir(self, path):
        self._send('MKCOL', path, 201)
    def rmdir(self, path):
        self.delete(str(path).rstrip('/') + '/')
    def delete(self, path):
        self._send('DELETE', path, 204)
    def upload(self, local_path, remote_path):
        with open(local_path, 'rb') as f:
            self._send('PUT', remote_path, (201, 204), data=f.read())
    def download(self, remote_path, local_path):
        response = self._send('GET', remote_path, 200)
        with open(local_path, 'wb') as f:
            #f.write(response.content)
            shutil.copyfileobj(response.raw, f)
