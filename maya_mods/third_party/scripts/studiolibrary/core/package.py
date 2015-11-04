# Embedded file name: C:/Users/hovel/Dropbox/packages/studiolibrary/1.8.6/build27/studiolibrary\core\package.py
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
import re
import utils
__all__ = ['Package']

class Package:

    def __init__(self):
        """
        """
        self._jsonUrl = ''
        self._helpUrl = ''
        self._version = '0.0.0'

    def openHelp(self):
        """
        :type:
        """
        import webbrowser
        webbrowser.open(self._helpUrl)

    def setJsonUrl(self, url):
        """
        :type url: str
        """
        self._jsonUrl = url

    def setHelpUrl(self, url):
        """
        :type url: str
        """
        self._helpUrl = url

    def helpUrl(self):
        """
        :rtype:
        """
        return self._helpUrl

    def jsonUrl(self):
        """
        :rtype: str
        """
        return self._jsonUrl

    def setVersion(self, version):
        """
        :type version: str
        """
        self._version = version

    def version(self):
        """
        :rtype: str
        """
        return self._version

    def latestVersion(self):
        """
        :rtype: str
        :raise:
        """
        try:
            data = utils.downloadUrl(self.jsonUrl())
            if data:
                if data.startswith('{'):
                    data = eval(data.strip(), {})
                    return data.get('version', self.version())
        except:
            raise

    def splitVersion(self, version = None):
        """
        :type version: str
        :rtype: (int, int, int)
        """
        version = version or self.version()
        reNumbers = re.compile('[0-9]+')
        major, miner, patch = [ int(reNumbers.search(value).group(0)) for value in version.split('.') ]
        return (major, miner, patch)

    def isUpdateAvailable(self):
        """
        :rtype: bool | None
        """
        latestVersion = self.latestVersion()
        if latestVersion:
            major1, miner1, patch1 = self.splitVersion()
            major2, miner2, patch2 = self.splitVersion(latestVersion)
            if major1 < major2:
                return True
            if major1 <= major2 and miner1 < miner2:
                return True
            if major1 <= major2 and miner1 <= miner2 and patch1 < patch2:
                return True
        return False


def test_package():
    """
    :rtype: None
    """
    jsonUrl = 'http://dl.dropbox.com/u/28655980/studiolibrary/studiolibrary.json'
    package = Package()
    package.setVersion('1.5.8')
    package.setJsonUrl(jsonUrl)
    print package.splitVersion()
    print package.latestVersion()
    print package.isUpdateAvailable()


if __name__ == '__main__':
    test_package()