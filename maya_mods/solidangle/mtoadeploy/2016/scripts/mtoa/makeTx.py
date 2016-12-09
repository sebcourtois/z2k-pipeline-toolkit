import glob
import os
import platform
import re
import subprocess
import maya.cmds as cmds
import shlex
from arnold import *
import pymel.versions as versions

# FIXME As of Arnold 4.2.13.6 the texture API functions have no binding yet
# so we'll temporarily provide bindings until this is resolved, see core #5293

AiTextureGetFormatFunc = ai.AiTextureGetFormat
AiTextureGetFormatFunc.argtypes = [AtString, POINTER(c_uint)]
AiTextureGetFormatFunc.restype = c_bool

def AiTextureGetFormat(filename):
    fmt = c_uint(0)
    success = AiTextureGetFormatFunc(filename, fmt)
    return int(fmt.value) if success else None

AiTextureGetBitDepthFunc = ai.AiTextureGetBitDepth
AiTextureGetBitDepthFunc.argtypes = [AtString, POINTER(c_uint)]
AiTextureGetBitDepthFunc.restype = c_bool

def AiTextureGetBitDepth(filename):
    bit_depth = c_uint(0)
    success = AiTextureGetBitDepthFunc(filename, bit_depth)
    return int(bit_depth.value) if success else None

AiTextureInvalidate = ai.AiTextureInvalidate
AiTextureInvalidate.argtypes = [AtString]

# startupinfo to prevent Windows processes to display a console window
if platform.system().lower() == 'windows':
    _no_window = subprocess.STARTUPINFO()
    _no_window.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    _no_window = None

## Compiled regex for expandFilename()
#_token_attr_rx = re.compile('<attr:[^>]*>')
#_token_udim_rx = re.compile('<udim:?[^>]*>')
#_token_tile_rx = re.compile('<tile:?[^>]*>')
_token_generic_rx = re.compile('<[^>]*>')

def expandFilename(filename):

    if filename.find('<') < 0:
        #no tokens, let's just return the filename in a single-element array
        return [filename]


    '''Return a list of image filenames with all tokens expanded.
       Since there is a long list of supported tokens, we're now searching for
       them in a more generic way (instead of specially looking for <udim>, <tile>, <attr:>)
    '''
    expand_glob = re.sub(_token_generic_rx, '*', filename)
    
#    expand_glob = re.sub(_token_udim_rx, '[1-9][0-9][0-9][0-9]', filename)
#    expand_glob = re.sub(_token_tile_rx, '_u[0-9]*_v[0-9]*', expand_glob)
#    expand_glob = re.sub(_token_attr_rx, '*', expand_glob)
    
    # testing AiTextureGetFormat to make sure the file is a valid image causes an image load.
    # Either we discard it after calling this function, or we simply don't do the check.
    # let's try the first option for now....
    filteredList = filter(lambda p: AiTextureGetFormat(p), glob.glob(expand_glob))
    for filteredImg in filteredList:
        if os.path.splitext(filteredImg)[1] != '.tx':
            # don't invalidate .tx files
            AiTextureInvalidate(filteredImg)

    return filteredList


def guessColorspace(filename):
    '''Guess the colorspace of the input image filename.
    @return: a string suitable for the --colorconvert option of maketx (linear, sRGB, Rec709)
    '''
    try:
        if AiTextureGetFormat(filename) == AI_TYPE_UINT and AiTextureGetBitDepth(filename) <= 16:
            return 'sRGB'
        else:
            return 'linear'

        # now discard the image file as AiTextureGetFormat has loaded it
        AiTextureInvalidate(filename)
    except:
        print '[maketx] Error: Could not guess colorspace for "%s"' % filename
        return 'linear'

## Compiled regexes for makeTx()
_maketx_rx_stats = re.compile('maketx run time \(seconds\):\s*(.+)')
_maketx_rx_noupdate = re.compile('no update required')
_maketx_binary = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin', 'maketx')
_maketx_cmd = [_maketx_binary, '-v', '-u', '--unpremult', '--oiio']

def makeTx(filename, colorspace='auto', arguments=''):
    '''Generate a TX texture with maketx
    '''

    # status[0] contains the amount of created tx files
    # status[1] the amount of skipped tx files
    # status[2] the amount of errors

    status = [0,0,0]
    if arguments == '':
        cmd = list(_maketx_cmd)
    else:
        cmd_str = _maketx_binary
        cmd_str += ' '
        cmd_str += arguments
        cmd = shlex.split(cmd_str, posix=False)

    maya_version = versions.shortName()
    if int(float(maya_version)) >= 2017:
        if cmds.colorManagementPrefs(q=True, cmEnabled=True):
            if colorspace in cmds.colorManagementPrefs(q=True, inputSpaceNames=True):
                if cmds.colorManagementPrefs(q=True, cmConfigFileEnabled=True):
                    color_config = cmds.colorManagementPrefs(q=True, configFilePath=True)
                else:
                    color_config = cmds.internalVar(userPrefDir=True)

                render_colorspace = cmds.colorManagementPrefs(q=True, renderingSpaceName=True)
                
                if colorspace != render_colorspace:
                    cmd += ['--colorengine', 'syncolor', '--colorconfig', color_config, '--colorconvert', colorspace, render_colorspace]
            else:
                # FIXME what should we do in auto mode ?
                if colorspace != 'auto':
                    print '[maketx] Warning: Invalid input colorspace "%s" for "%s", disabling color conversion' % (colorspace, filename)

    for tile in expandFilename(filename):
        if os.path.splitext(tile)[1] == '.tx':
            print '[maketx] Skipping native TX texture: %s' % tile
            status[1] += 1
            continue

        if colorspace == 'auto':
            colorspace = guessColorspace(tile)
        
        outputTx = os.path.splitext(tile)[0] + '.tx'
        AiTextureInvalidate(outputTx)

        res = subprocess.Popen(cmd + [tile], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window).communicate()[0]

        if re.search(_maketx_rx_noupdate, res):
            # we don't want to get messages saying that texture is up-to-date, mainly
            # with auto-tx since this happens at every render.
            # If we really want it for txManager we can add an argument in this function
            # and re-introduce the print

            #print '[maketx] TX texture is up to date for "%s" (%s)' % (tile, colorspace)
            status[1] += 1
        else:
            mo = re.search(_maketx_rx_stats, res)
            if mo:
                print '[maketx] Generated TX for "%s" (%s) in %s seconds' % (tile, colorspace, mo.group(1))
                AiTextureInvalidate(outputTx) 
                status[0] += 1
            else:
                print '[maketx] Error: Could not generate TX for "%s" (%s)' % (tile, colorspace)
                print res
                status[2] += 1
       
    return status
