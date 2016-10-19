import pymel.core as pm
import mtoa.core as core
from mtoa.core import createStandIn, createVolume
from mtoa.ui.ae.aiStandInTemplate import LoadStandInButtonPush
import mtoa.utils as mutils
import maya.cmds as cmds
import mtoa.txManager
import mtoa.lightManager
import mtoa.renderToTexture
import arnold as ai
import pymel.versions as versions

from uuid import getnode as get_mac
import os
import shutil
import sys

def doCreateStandInFile():
    node = createStandIn()
    LoadStandInButtonPush(node.name())

def doExportStandIn():
    #Save the defaultType
    default = cmds.optionVar(q='defaultFileExportActiveType')
    try:
        #Change it to ASS
        cmds.optionVar(sv=('defaultFileExportActiveType', "ASS Export"))
        pm.mel.eval('ExportSelection')
    finally:
        cmds.optionVar(sv=('defaultFileExportActiveType', default))

def doExportOptionsStandIn():
    pm.mel.eval('ExportSelectionOptions')
    pm.mel.eval('setCurrentFileTypeOption ExportActive "" "ASS Export"')
    
def doCreateMeshLight():
    sls = cmds.ls(sl=True, et='transform')
    if len(sls) == 0:
        cmds.confirmDialog(title='Error', message='No transform is selected!', button='Ok')
        return
    shs = cmds.listRelatives(sls[0], type='mesh')
    if shs is None:
        cmds.confirmDialog(title='Error', message='The selected transform has no meshes', button='Ok')
        return
    elif len(shs) == 0:
        cmds.confirmDialog(title='Error', message='The selected transform has no meshes', button='Ok')
        return
    cmds.setAttr('%s.aiTranslator' % shs[0], 'mesh_light', type='string')

    
def arnoldAboutDialog():
    legaltext = "All use of this Software is subject to the terms and conditions of the software license agreement accepted upon installation of this Software and/or packaged with the Software.\n\
\n\
Third-Party Software Credits and Attributions\n\
\n\
Portions related to OpenImageIO Copyright 2008-2015 Larry Gritz et al. All Rights Reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  * Neither the name of the software's owners nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to IlmBase Copyright (c) 2002-2011, Industrial Light & Magic, a division of Lucasfilm Entertainment Company Ltd. All rights reserved. Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  Neither the name of Industrial Light & Magic nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to libjpeg (C) 1991-1998, Thomas G. Lane. All Rights Reserved except as specified below. The authors make NO WARRANTY or representation, either express or implied, with respect to this software, its quality, accuracy, merchantability, or fitness for a particular purpose. This software is provided \"AS IS\", and you, its user, assume the entire risk as to its quality and accuracy. Permission is hereby granted to use, copy, modify, and distribute this software (or portions thereof) for any purpose, without fee, subject to these conditions:  (1) If any part of the source code for this software is distributed, then this README file must be included, with this copyright and no-warranty notice unaltered; and any additions, deletions, or changes to the original files must be clearly indicated in accompanying documentation. (2) If only executable code is distributed, then the accompanying documentation must state that \"this software is based in part on the work of the Independent JPEG Group\". (3) Permission for use of this software is granted only if the user accepts full responsibility for any undesirable consequences; the authors accept NO LIABILITY for damages of any kind. These conditions apply to any software derived from or based on the IJG code, not just to the unmodified library. If you use our work, you ought to acknowledge us. Permission is NOT granted for the use of any IJG author's name or company name in advertising or publicity relating to this software or products derived from it. This software may be referred to only as \"the Independent JPEG Group's software\". We specifically permit and encourage the use of this software as the basis of commercial products, provided that all warranty or liability claims are assumed by the product vendor. ansi2knr.c is included in this distribution by permission of L. Peter Deutsch, sole proprietor of its copyright holder, Aladdin Enterprises of Menlo Park, CA. ansi2knr.c is NOT covered by the above copyright and conditions, but instead by the usual distribution terms of the Free Software Foundation; principally, that you must include source code if you redistribute it. (See the file ansi2knr.c for full details). However, since ansi2knr.c is not needed as part of any program generated from the IJG code, this does not limit you more than the foregoing paragraphs do. We are required to state that \"The Graphics Interchange Format(c) is the Copyright property of CompuServe Incorporated. GIF(sm) is a Service Mark property of CompuServe Incorporated.\"\n\
\n\
Portions related to libtiff Copyright (c) 1988-1997 Sam Leffler.  Copyright (c) 1991-1997 Silicon Graphics, Inc.  Permission to use, copy, modify, distribute, and sell this software and its documentation for any purpose is hereby granted without fee, provided that (i) the above copyright notices and this permission notice appear in all copies of the software and related documentation, and (ii) the names of Sam Leffler and Silicon Graphics may not be used in any advertising or publicity relating to the software without the specific, prior written permission of Sam Leffler and Silicon Graphics.  THE SOFTWARE IS PROVIDED \"AS-IS\" AND WITHOUT WARRANTY OF ANY KIND, EXPRESS, IMPLIED OR OTHERWISE, INCLUDING WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  IN NO EVENT SHALL SAM LEFFLER OR SILICON GRAPHICS BE LIABLE FOR ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\n\
\n\
Portions related to OpenEXR Copyright (c) 2002-2011, Industrial Light & Magic, a division of Lucasfilm Entertainment Company Ltd. All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  Neither the name of Industrial Light & Magic nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to zlib Copyright (C) 1995-2013 Jean-loup Gailly and Mark Adler. This software is provided 'as-is', without any express or implied warranty.  In no event will the authors be held liable for any damages arising from the use of this software.  Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:  1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.  2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software. 3. This notice may not be removed or altered from any source distribution.  THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\
\n\
Portions related to OpenSubdiv Copyright (C) 2013 Pixar.  Licensed under the Apache License, Version 2.0 (the \"Apache License\") with the following modification; you may not use this file except in compliance with the Apache License and the following modification to it: Section 6. Trademarks. is deleted and replaced with: 6. Trademarks. This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor and its affiliates, except as required to comply with Section 4(c) of the License and to reproduce the content of the NOTICE file.  You may obtain a copy of the Apache License at http://www.apache.org/licenses/LICENSE-2.0.  Unless required by applicable law or agreed to in writing, software distributed under the Apache License with the above modification is distributed on an \"AS IS\" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the Apache License for the specific language governing permissions and limitations under the Apache License.  \n\
\n\
Portions related to gperftools Copyright (C) 2005 Google Inc.  All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  * Neither the name of Google Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to OpenVDB Copyright (c) 2012-2013 DreamWorks Animation LLC.  All rights reserved. This software is distributed under the Mozilla Public License 2.0 (http://www.mozilla.org/MPL/2.0/).  Redistributions of source code must retain the above copyright and license notice and the following restrictions and disclaimer.  Neither the name of DreamWorks Animation nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  IN NO EVENT SHALL THE COPYRIGHT HOLDERS' AND CONTRIBUTORS' AGGREGATE LIABILITY FOR ALL CLAIMS REGARDLESS OF THEIR BASIS EXCEED US$250.00. A text copy of this license and the source code for OpenVDB (and modifications made by Solid Angle, if any) can be found at the Autodesk website www.autodesk.com/lgplsource.\n\
\n\
Portions related to Boost Permission is hereby granted, free of charge, to any person or organization obtaining a copy of the software and accompanying documentation covered by this license (the \"Software\") to use, reproduce, display, distribute, execute, and transmit the Software, and to prepare derivative works of the Software, and to permit third-parties to whom the Software is furnished to do so, all subject to the following:  The copyright notices in the Software and this entire statement, including the above license grant, this restriction and the following disclaimer, must be included in all copies of the Software, in whole or in part, and all derivative works of the Software, unless such copies or derivative works are solely in the form of machine-executable object code generated by a source language processor.  THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\
\n\
Portions related to pystring Copyright (c) 2008-2010, Sony Pictures Imageworks Inc.  All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  Neither the name of the organization Sony Pictures Imageworks nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to dirent Copyright (c) 1999-2003 Apple Computer, Inc.  All Rights Reserved.  This file contains Original Code and/or Modifications of Original Code as defined in and that are subject to the Apple Public Source License Version 2.0 (the 'License'). You may not use this file except in compliance with the License. Please obtain a copy of the License at http://www.opensource.apple.com/apsl/ and read it before using this file.  The Original Code and all software distributed under the License are distributed on an 'AS IS' basis, WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, AND APPLE HEREBY DISCLAIMS ALL SUCH WARRANTIES, INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, QUIET ENJOYMENT OR NON-INFRINGEMENT.  Please see the License for the specific language governing rights and limitations under the License.\n\
\n\
Portions related to dirent Copyright (c) 1989, 1993 The Regents of the University of California.  All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. 3. All advertising materials mentioning features or use of this software must display the following acknowledgement:  This product includes software developed by the University of California, Berkeley and its contributors. 4. Neither the name of the University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.  THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION).  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to OpenColorIO Copyright (c) 2003-2010 Sony Pictures Imageworks Inc., et al. All Rights Reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. Neither the name of Sony Pictures Imageworks nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to Pystring is part of OpenColorIO Copyright (c) 2008-2010, Sony Pictures Imageworks Inc All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. Neither the name of the organization Sony Pictures Imageworks nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
Portions related to yaml-cpp that is part of OpenColorIO Copyright (c) 2008 Jesse Beder.  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\
\n\
Portions related to PTEX software that is part of OpenColorIO 2009 Disney Enterprises, Inc. All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.  The names \"Disney\", \"Walt Disney Pictures\", \"Walt Disney Animation Studios\" or the names of its contributors may NOT be used to endorse or promote products derived from this software without specific prior written permission from Walt Disney Pictures. Disclaimer: THIS SOFTWARE IS PROVIDED BY WALT DISNEY PICTURES AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT AND TITLE ARE DISCLAIMED. IN NO EVENT SHALL WALT DISNEY PICTURES, THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND BASED ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.\n\
\n\
Portions related to Little CMS that is part of OpenColorIO Copyright (c) 1998-2010 Marti Maria Saguer.  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\
\n\
Portions related to argparse that is part of OpenColorIO Copyright 2008 Larry Gritz and the other authors and contributors. All Rights Reserved. Based on BSD-licensed software Copyright 2004 NVIDIA Corp.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met: * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer. * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution. * Neither the name of the software\"s owners nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS \"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\
\n\
\n\
\n\
\n"
    
    
    
    
    arnoldAboutText =  u"Arnold for Maya\n\n"
    arnoldAboutText += "MtoA " + cmds.pluginInfo( 'mtoa', query=True, version=True)
    arnoldMercurialID = cmds.arnoldPlugins(getMercurialID=True)
    if not '(Master)' in arnoldMercurialID:
        arnoldAboutText += " - " + arnoldMercurialID
    arnoldAboutText += "\nArnold Core "+".".join(ai.AiGetVersion())+"\n\n"
    arnoldAboutText += u"Copyright (c) 2001-2009 Marcos Fajardo and\nCopyright (c) 2009-2016 Solid Angle  S.L.\nAll rights reserved\n\n"
    arnoldAboutText += u"Developed by: Ángel Jimenez, Olivier Renouard, Yannick Puech,\nBorja Morales, Nicolas Dumay, Pedro Fernando Gomez,\nPál Mezei, Sebastien Ortega\n\n"
    arnoldAboutText += u"Acknowledgements: Javier González, Miguel González, Lee Griggs,\nChad Dombrova, Gaetan Guidet, Gaël Honorez, Diego Garcés,\nKevin Tureski, Frédéric Servant, Darin Grant"

    if (cmds.window("AboutArnold", ex=True)):
        cmds.deleteUI("AboutArnold")
    w = cmds.window("AboutArnold", title="About")
    cmds.window("AboutArnold", edit=True, width=520, height=550)
    cmds.rowColumnLayout( numberOfColumns=4, columnWidth=[(1,20), (2, 52), (3, 50), (4, 380)] )

    cmds.text(label="");cmds.text(label="");cmds.text(label="");cmds.text(label="")

    cmds.text(label="")
    cmds.image(image="MtoA_Logo.png")
    cmds.text(label="")
    cmds.text(align="left",label=arnoldAboutText)

    cmds.text(label="");cmds.text(label="");cmds.text(label="");cmds.text(label="")
    
    cmds.text(label="");cmds.text(label="");cmds.text(label="");
    
    cmds.scrollField(editable=False, wordWrap=True, font="plainLabelFont", height=200, text=legaltext)
    
    cmds.text(label="");cmds.text(label="");cmds.text(label="");cmds.text(label="")

    cmds.text(label="");cmds.text(label="\n");cmds.text(label="");cmds.text(label="")

    cmds.text(label="")
    cmds.text(label="")
    cmds.button( width=150,label='OK', command=('import maya.cmds as cmds;cmds.deleteUI(\"' + w + '\", window=True)') )
    cmds.setParent( '..' )
    
    cmds.showWindow(w)
    
def dotDotDotButtonPush(file):
    licenseFilter = 'License Files (*.lic)'
    ret = cmds.fileDialog2(fileFilter=licenseFilter, 
                            cap='Load License File',okc='Load',fm=1)
    if ret is not None and len(ret):
        cmds.textField(file, edit=True, text=ret[0])
        
def installButtonPush(file):
    licenseFile = cmds.textField(file, query=True, text=True)
    import maya.mel as mel
    mPath = mel.eval('getenv "MTOA_PATH"')
    destination = os.path.join(mPath,'bin')
    try:
        shutil.copy(licenseFile,destination)
        cmds.confirmDialog(title='Success', message='License Successfully Installed', button=['Ok'], defaultButton='Ok' )
    except:
        cmds.arnoldCopyAsAdmin(f=licenseFile,o=destination)
    
def arnoldLicenseDialog():
    if (cmds.window("ArnoldLicense", ex=True)):
        cmds.deleteUI("ArnoldLicense")
    w = cmds.window("ArnoldLicense", title="Arnold Node-locked License")
    cmds.window("ArnoldLicense", edit=True, width=430, height=280)
    cmds.columnLayout()
    cmds.rowColumnLayout( numberOfColumns=2, columnWidth=[(1,10), (2, 412)] )

    cmds.text(label="");cmds.text(label="");

    arnoldAboutText =  u"A node-locked license allows you to render with Arnold on one computer only.\n"

    cmds.text(label="")
    cmds.text(align="left",label=arnoldAboutText)

    cmds.text(label="")
    cmds.text(label="")

    cmds.separator()
    cmds.separator()

    cmds.setParent( '..' )
    cmds.separator()

    cmds.rowColumnLayout( numberOfColumns=2, columnWidth=[(1,10), (2, 412)] )
    macText =  u"To issue a node-locked license, we need the MAC address of your computer.\n"
    cmds.text(label="")
    cmds.text(align="left",label=macText)
    cmds.setParent( '..' )
    cmds.separator()

    cmds.rowColumnLayout( numberOfColumns=6, columnWidth=[(1,10),(2,90), (3, 190),(4,40),(5,80),(6,12)] )
    cmds.text(label="")
    cmds.text(align="left",label="MAC Address")
    name = cmds.textField()
    mac = get_mac()
    mactext = ("%012X" % mac)
    cmds.textField(name,  edit=True, text=mactext, editable=False )
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")

    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")

    cmds.separator()
    cmds.separator()
    cmds.separator()
    cmds.separator()
    cmds.separator()
    cmds.separator()

    cmds.setParent( '..' )

    cmds.rowColumnLayout( numberOfColumns=2, columnWidth=[(1,10), (2, 412)] )
    macText =  u"To install your node-locked license, locate the license file (.lic) and click Install.\n"
    cmds.text(label="")
    cmds.text(align="left",label=macText)
    cmds.setParent( '..' )

    cmds.rowColumnLayout( numberOfColumns=8, columnWidth=[(1,10),(2,90),(3,190),(4,7),(5,26),(6,7),(7,80),(8,12)] )
    cmds.text(label="")
    cmds.text(align="left",label="License file (.lic)")
    file = cmds.textField()
    cmds.text(label="")
    cmds.button( label='...', command=lambda *args: dotDotDotButtonPush(file) )
    cmds.text(label="")
    cmds.button( label='Install', command=lambda *args: installButtonPush(file) )
    cmds.text(label="")

    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")

    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")
    cmds.text(label="")

    cmds.setParent( '..' )

    cmds.rowColumnLayout( numberOfColumns=5, columnWidth=[(1,80),(2,160), (3, 80),(4,20),(5,80)] )
    cmds.text(label="")
    cmds.text(label="")
    cmds.button( label='Close', command=('import maya.cmds as cmds;cmds.deleteUI(\"' + w + '\", window=True)'))
    cmds.text(label="")
    cmds.button( label='Help', c=lambda *args: cmds.launch(webPage='https://www.solidangle.com/support/licensing/'))

    cmds.setParent( '..' )

    cmds.showWindow(w)
    
def arnoldTxManager():
    core.createOptions()
    win = mtoa.txManager.MtoATxManager()
    win.create()
    win.refreshList()
    
def arnoldLightManager():
    win = mtoa.lightManager.MtoALightManager()
    win.create()

def arnoldBakeGeo():
    objFilter = "Obj File (*.obj)"
    ret = cmds.fileDialog2(cap='Bake Selection as OBJ', fm=0, ff=objFilter)
    if ret is not None and len(ret):
        cmds.arnoldBakeGeo(f=ret[0])

def arnoldRenderToTexture():
    selList = cmds.ls(sl=1)
    if (len(selList) == 0):
        cmds.confirmDialog( title='Render To Texture', message='No Geometry Selected', button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )
        return False

    win = mtoa.renderToTexture.MtoARenderToTexture()
    win.create()

def arnoldMtoARenderView():
    # core.ACTIVE_CAMERA is not set, anything we could do here ?
    #if core.ACTIVE_CAMERA != None:
    #    cmds.arnoldRenderView(cam=core.ACTIVE_CAMERA)
    # so instead we're calling it without any argument

    core.createOptions()
    cmds.arnoldRenderView()

def createArnoldMenu():
    # Add an Arnold menu in Maya main window
    if not pm.about(b=1):
        maya_version = versions.shortName()
        if int(float(maya_version)) < 2017:
            pm.menu('ArnoldMenu', label='Arnold', parent='MayaWindow', tearOff=True )
        else:
            pm.menu('ArnoldMenu', label='Arnold', parent='MayaWindow', tearOff=True, version="2017" )

        pm.menuItem('ArnoldMtoARenderView', label='Arnold RenderView', parent='ArnoldMenu',
                    c=lambda *args: arnoldMtoARenderView())
        pm.menuItem(parent='ArnoldMenu', divider=True)

        pm.menuItem('ArnoldStandIn', label='StandIn', parent='ArnoldMenu', subMenu=True, tearOff=True)
        pm.menuItem('ArnoldCreateStandIn', parent='ArnoldStandIn', label="Create",
                    c=lambda *args: createStandIn())
        pm.menuItem('ArnoldCreateStandInFile', parent='ArnoldStandIn', optionBox=True,
                    c=lambda *args: doCreateStandInFile())
        pm.menuItem('ArnoldExportStandIn', parent='ArnoldStandIn', label='Export',
                    c=lambda *args: doExportStandIn())
        pm.menuItem('ArnoldExportOptionsStandIn', parent='ArnoldStandIn', optionBox=True,
                    c=lambda *args: doExportOptionsStandIn())

        pm.menuItem('ArnoldLights', label='Lights', parent='ArnoldMenu', subMenu=True, tearOff=True)
        
        pm.menuItem('ArnoldAreaLights', parent='ArnoldLights', label="Area Light",
                    c=lambda *args: mutils.createLocator('aiAreaLight', asLight=True))
        pm.menuItem('SkydomeLight', parent='ArnoldLights', label="Skydome Light",
                    c=lambda *args: mutils.createLocator('aiSkyDomeLight', asLight=True))
        pm.menuItem('ArnoldMeshLight', parent='ArnoldLights', label='Mesh Light',
                    c=lambda *args: doCreateMeshLight())
        pm.menuItem('PhotometricLights', parent='ArnoldLights', label="Photometric Light",
                    c=lambda *args: mutils.createLocator('aiPhotometricLight', asLight=True))

        pm.menuItem(parent='ArnoldLights', divider=True)

        pm.menuItem('MayaDirectionalLight', parent='ArnoldLights', label="Maya Directional Light",
                    c=lambda *args: cmds.CreateDirectionalLight())
        pm.menuItem('MayaPointLight', parent='ArnoldLights', label="Maya Point Light",
                    c=lambda *args: cmds.CreatePointLight())
        pm.menuItem('MayaSpotLight', parent='ArnoldLights', label="Maya Spot Light",
                    c=lambda *args: cmds.CreateSpotLight())
        pm.menuItem('MayaQuadLight', parent='ArnoldLights', label="Maya Quad Light",
                    c=lambda *args: cmds.CreateAreaLight())
                    
        pm.menuItem('ArnoldVolume', label='Volume', parent='ArnoldMenu',
                    c=lambda *args: createVolume())
                    
        pm.menuItem('ArnoldFlush', label='Flush Caches', parent='ArnoldMenu', subMenu=True, tearOff=True)
        pm.menuItem('ArnoldFlushTexture', parent='ArnoldFlush', label="Textures",
                    c=lambda *args: cmds.arnoldFlushCache(textures=True))
        pm.menuItem('ArnoldFlushBackground', parent='ArnoldFlush', label="Skydome Lights",
                    c=lambda *args: cmds.arnoldFlushCache(skydome=True))
        pm.menuItem('ArnoldFlushQuads', parent='ArnoldFlush', label="Quad Lights",
                    c=lambda *args: cmds.arnoldFlushCache(quads=True))
        pm.menuItem('ArnoldFlushAll', parent='ArnoldFlush', label="All",
                    c=lambda *args: cmds.arnoldFlushCache(flushall=True))
                    
        pm.menuItem('ArnoldUtilities', label='Utilities', parent='ArnoldMenu', subMenu=True, tearOff=True)
        pm.menuItem('ArnoldBakeGeo', label='Bake Selected Geometry', parent='ArnoldUtilities',
                    c=lambda *args: arnoldBakeGeo())
        pm.menuItem('ArnoldRenderToTexture', label='Render Selection To Texture', parent='ArnoldUtilities',
                    c=lambda *args: arnoldRenderToTexture())
        pm.menuItem('ArnoldTxManager', label='Tx Manager', parent='ArnoldUtilities',
                    c=lambda *args: arnoldTxManager())                    
        pm.menuItem('ArnoldLightManager', label='Light Manager', parent='ArnoldUtilities',
                    c=lambda *args: arnoldLightManager())

        pm.menuItem('ArnoldHelpMenu', label='Help', parent='ArnoldMenu',
                    subMenu=True, tearOff=True)

        pm.menuItem('ArnoldUserGuide', label='User Guide', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://support.solidangle.com/display/AFMUG/Arnold+for+Maya+User+Guide'))

        pm.menuItem('ArnoldTutorials', label='Common Workflows', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://support.solidangle.com/display/AFMUG/Common+Workflows'))

        pm.menuItem('ArnoldVideos', label='Videos', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://support.solidangle.com/display/AFMUG/Video+Tutorials'))

        pm.menuItem(divider=1, parent='ArnoldHelpMenu')

        pm.menuItem('ArnoldSolidAngle', label='Solid Angle', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://www.solidangle.com'))

        pm.menuItem('ArnoldMailingLists', label='Mailing Lists', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://subscribe.solidangle.com'))

        pm.menuItem('ArnoldAsk', label='Knowledge Base', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://ask.solidangle.com'))

        pm.menuItem('ArnoldSupportBlog', label='Support Blog', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://support.solidangle.com/blog/arnsupp'))

        pm.menuItem('ArnoldLicensing', label='Licensing', parent='ArnoldHelpMenu',
                    c=lambda *args: arnoldLicenseDialog())

        pm.menuItem(divider=1, parent='ArnoldHelpMenu')

        pm.menuItem('ArnoldDeveloperGuide', label='Developer Guide', parent='ArnoldHelpMenu',
                    c=lambda *args: cmds.launch(webPage='https://support.solidangle.com/display/ARP/Arnoldpedia'))
                    
        pm.menuItem('ArnoldAbout', label='About', parent='ArnoldMenu',
                    c=lambda *args: arnoldAboutDialog())
