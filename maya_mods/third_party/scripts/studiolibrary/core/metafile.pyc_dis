# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\metafile.py
"""
Released subject to the BSD License
Please visit http://www.voidspace.org.uk/python/license.shtml

Contact: kurt.rathjen@gmail.com
Comments, suggestions and bug reports are welcome.
Copyright (c) 2015, Kurt Rathjen, All rights reserved.

It is a very non-restrictive license but it comes with the usual disclaimer.
This is free software: test it, break it, just don't blame me if it eats your
data! Of course if it does, let me know and I'll fix the problem so that it
doesn't happen to anyone else.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
   # * Redistributions of source code must retain the above copyright
   #   notice, this list of conditions and the following disclaimer.
   # * Redistributions in binary form must reproduce the above copyright
   # notice, this list of conditions and the following disclaimer in the
   # documentation and/or other materials provided with the distribution.
   # * Neither the name of Kurt Rathjen nor the
   # names of its contributors may be used to endorse or promote products
   # derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY KURT RATHJEN ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL KURT RATHJEN BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""
import time
import getpass
import logging
import basepath
import shortuuid
__all__ = ['MetaFile']
logger = logging.getLogger(__name__)

class MetaFile(basepath.BasePath):

    def __init__(self, path, read = True):
        """
        :type path: str
        :type read: bool
        """
        super(MetaFile, self).__init__(path)
        self._uuid = None
        self._errors = ''
        if read and self.exists():
            self.read()
        return

    def uuid(self):
        """
        :rtype: str
        """
        return self.get('uuid', '')

    def errors(self):
        """
        :rtype: str
        """
        return self._errors

    def setErrors(self, text):
        """
        :type text: str
        """
        self._errors = text

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

    def read(self):
        """
        :rtype: dict[]
        """
        data = self._read()
        self.data().update(data)
        return self.data()

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

    def _read(self):
        """
        :rtype: dict[]
        """
        results = {}
        f = open(self.path(), 'r')
        data = f.read()
        f.close()
        try:
            results = eval(data.strip(), {})
        except Exception as e:
            import traceback
            msg = "Error while reading MetaFile '%s'\n" % self.path()
            msg += traceback.format_exc() + str(e)
            logger.info(msg)
            self.setErrors(msg)

        return results

    @staticmethod
    def write(path, data):
        """
        :type path: str
        :type data: str
        :rtype: dict[]
        """
        f = open(path, 'w')
        f.write(str(data))
        f.close()

    def updateNonEditables(self):
        """
        :rtype: None
        """
        if self.exists():
            logger.debug("Updating non editables '%s'" % self.path())
            data = self._read()
            if 'uuid' in data:
                self.set('uuid', data['uuid'])
            if 'ctime' in data:
                self.set('ctime', data['ctime'])

    def save(self):
        """
        :rtype: None
        """
        self.updateNonEditables()
        path = self.path()
        data = self.data()
        t = str(time.time()).split('.')[0]
        owner = getpass.getuser().lower()
        if 'ctime' not in data:
            data['ctime'] = t
        if 'uuid' not in data:
            data['uuid'] = shortuuid.ShortUUID().uuid()
        data['mtime'] = t
        data['owner'] = owner
        logger.debug("Saving Meta File '%s'" % self.path())
        self.mkdir()
        try:
            newData_ = eval(str(data), {})
            self.write(path, data=newData_)
        except:
            import traceback
            data['errors'].append(traceback.format_exc())
            raise IOError('An error has occurred when evaluating string: %s' % str(self))