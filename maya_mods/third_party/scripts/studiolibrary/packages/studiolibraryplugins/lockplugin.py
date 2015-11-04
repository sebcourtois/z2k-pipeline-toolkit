#!/usr/bin/python
"""
Released subject to the BSD License
Please visit http://www.voidspace.org.uk/python/license.shtml

Contact: kurt.rathjen@gmail.com
Comments, suggestions and bug reports are welcome.
Copyright (c) 2014, Kurt Rathjen, All rights reserved.

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
import studiolibrary


class Plugin(studiolibrary.Plugin):

    def __init__(self, *args, **kwargs):
        """
        :type args:
        """
        studiolibrary.Plugin.__init__(self, *args, **kwargs)
        self.setName("lock")  # Must set a name for the plugin
        self.setIconPath(self.dirname() + "/resource/images/lock.png")

        self._superusers = []
        self._lockFolder = re.compile("")
        self._unlockFolder = re.compile("")

    # Override the load method so that it doesn't show in the "+" new menu
    def load(self):
        """
        """
        if self.libraryWidget():
            # Check what kwargs were used in the studiolibrary.main() function
            self._superusers = self.libraryWidget().kwargs().get("superusers", [])
            self._lockFolder = re.compile(self.libraryWidget().kwargs().get("lockFolder", ""))
            self._unlockFolder = re.compile(self.libraryWidget().kwargs().get("unlockFolder", ""))
            self.updateLock()

    def folderSelectionChanged(self, itemSelection1, itemSelection2):
        """
        :type itemSelection1:
        :type itemSelection2:
        """
        self.updateLock()

    def updateLock(self):    
        """
        :rtype: None
        """
        if studiolibrary.user() in self._superusers or []:
            self.libraryWidget().setLocked(False)
            return

        if self._lockFolder.match("") and self._unlockFolder.match(""):
            if self._superusers:  # Lock if only the superusers arg is used
                self.libraryWidget().setLocked(True)
            else:  # Unlock if no keyword arguments are used
                self.libraryWidget().setLocked(False)
            return

        folders = self.libraryWidget().selectedFolders()

        # Lock the selected folders that match the self._lockFolder regx
        if not self._lockFolder.match(""):
            for folder in folders or []:
                if self._lockFolder.search(folder.path()):
                    self.libraryWidget().setLocked(True)
                    return
            self.libraryWidget().setLocked(False)

        # Unlock the selected folders that match the self._unlockFolder regx
        if not self._unlockFolder.match(""):
            for folder in folders or []:
                if self._unlockFolder.search(folder.path()):
                    self.libraryWidget().setLocked(False)
                    return
            self.libraryWidget().setLocked(True)


if __name__ == "__main__":

    import studiolibrary
    # root = "P:/figaro/studiolibrary/anim"
    # name = "Figaro Pho - Anim"
    superusers = ["kurt.rathjen"]
    plugins = ["examplePlugin"]

    # Lock all folders unless you're a superuser.
    studiolibrary.main(superusers=superusers, plugins=plugins, add=True)

    # This command will lock only folders that contain the word "Approved" in their path.
    # studiolibrary.main(name=name, root=root, superusers=superusers, lockFolder="Approved")

    # This command will lock all folders except folders that contain the words "Users" or "Shared" in their path.
    # studiolibrary.main(name=name, root=root, superusers=superusers, unlockFolder="Users|Shared")
