# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\tempdir.py
"""
Released subject to the BSD License
Please visit http://www.voidspace.org.uk/python/license.shtml

Contact: kurt.rathjen@gmail.com
Comments, suggestions and bug reports are welcome.
Copyright (c) 2015, Kurt Rathjen, All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
 * Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
 * Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
 * Neither the name of Kurt Rathjen nor the names of its contributors may
   be used to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY KURT RATHJEN ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL KURT RATHJEN BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import os
import shutil
import getpass
import tempfile
__all__ = ['TempDir']

class TempDir:

    def __init__(self, *args, **kwargs):
        """
        :type subDirs: list[str]
        """
        user = getpass.getuser().lower()
        tempdir = tempfile.gettempdir().replace('\\', '/')
        self._path = os.path.join(tempdir, 'studiolibrary', user, *args)
        if kwargs.get('clean', False):
            self.clean()
        if kwargs.get('makedirs', True):
            self.makedirs()

    def path(self):
        """
        :rtype: str
        """
        return self._path

    def clean(self):
        """
        :rtype: str
        """
        if os.path.exists(self.path()):
            shutil.rmtree(self.path())

    def makedirs(self):
        """
        :rtype: str
        """
        if not os.path.exists(self.path()):
            os.makedirs(self.path())