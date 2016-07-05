# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.13.0/build27/studiolibrary\core\metafile.py
import time
import getpass
import logging
from . import basepath
__all__ = ['MetaFile']
logger = logging.getLogger(__name__)

class MetaFile(basepath.BasePath):

    def __init__(self, path, read = True):
        """
        :type path: str
        :type read: bool
        """
        super(MetaFile, self).__init__(path)
        self._data = {}
        if read and self.exists():
            self.read()

    def data(self):
        """
        :rtype: dict
        """
        return self._data

    def setData(self, data):
        """
        :type data: dict
        :rtype: None
        """
        self._data = data

    def set(self, key, value):
        """
        :type key: str
        :type value: object
        """
        self.data()[key] = value

    def setdefault(self, key, value):
        """
        :type key: str
        :type value: object
        """
        self.data().setdefault(key, value)

    def get(self, key, default = None):
        """
        :type key: str
        :type default: object
        """
        return self.data().get(key, default)

    def setDescription(self, text):
        """
        :type text: str
        """
        self.set('description', text)

    def description(self):
        """
        :rtype: str
        """
        return self.get('description', '')

    def owner(self):
        """
        :rtype: str
        """
        return self.get('owner', '')

    def mtime(self):
        """
        :rtype: str
        """
        return self.get('mtime', '')

    def ctime(self):
        """
        :rtype: str
        """
        return self.get('ctime', '')

    def read(self):
        """
        :rtype: dict[]
        """
        data = self._read()
        self.data().update(data)
        return self.data()

    def _read(self):
        """
        :rtype: dict
        """
        results = {}
        with open(self.path(), 'r') as f:
            data = f.read()
            try:
                results = eval(data.strip(), {})
            except Exception as msg:
                logger.exception(msg)

        return results

    def _write(self, data):
        """
        :type data: str
        :rtype: dict
        """
        with open(self.path(), 'w') as f:
            f.write(str(data))

    def save(self):
        """
        :rtype: None
        """
        data = self.data()
        t = str(time.time()).split('.')[0]
        owner = getpass.getuser().lower()
        if 'ctime' not in data:
            data['ctime'] = t
        data['mtime'] = t
        data['owner'] = owner
        logger.debug("Saving Meta File '%s'" % self.path())
        self.mkdir()
        try:
            data_ = eval(str(data), {})
            self._write(data=data_)
        except:
            msg = 'An error has occurred when evaluating string: {0}'
            msg = msg.format(str(data))
            raise IOError(msg)