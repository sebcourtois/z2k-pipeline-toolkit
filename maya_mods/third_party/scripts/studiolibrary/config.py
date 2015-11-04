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
import os
import studiolibrary


studiolibrary.Library.DEFAULT_PLUGINS = ["studiolibraryplugins.lockplugin",
                                         "studiolibraryplugins.poseplugin",
                                         "studiolibraryplugins.animationplugin",
                                         "studiolibraryplugins.mirrortableplugin",
                                         "studiolibraryplugins.selectionsetplugin"
                                         ]

# studiolibrary.Library.DEFAULT_COLOR = "rgb(0,200,100)"
# studiolibrary.Library.DEFAULT_BACKGROUND_COLOR = "rgb(60,100,180)"

studiolibrary.CHECK_FOR_UPDATES_ENABLED = True

studiolibrary.Analytics.ENABLED = True
studiolibrary.Analytics.DEFAULT_ID = "UA-50172384-1"

studiolibrary.FoldersWidget.CACHE_ENABLED = True
studiolibrary.FoldersWidget.SELECT_CHILDREN_ENABLED = False

studiolibrary.Settings.DEFAULT_PATH = os.getenv('APPDATA') or os.getenv('HOME')
studiolibrary.Settings.DEFAULT_PATH += "/studiolibrary"

# Meta paths and version paths are camel case for legacy reasons
studiolibrary.Record.META_PATH = "<PATH>/.studioLibrary/record.dict"
studiolibrary.Folder.META_PATH = "<PATH>/.studioLibrary/folder.dict"
studiolibrary.Folder.ORDER_PATH = "<PATH>/.studioLibrary/order.list"

studiolibrary.MasterPath.VERSION_CONTROL_ENABLED = True
studiolibrary.MasterPath.VERSION_PATH = "<DIRNAME>/.studioLibrary/<NAME><EXTENSION>/<NAME><VERSION><EXTENSION>"
