
from ctypes import *
from .arnold_common import ai
from .ai_types import *
from .ai_node_entry import *

AiTextureGetResolutionFunc = ai.AiTextureGetResolution
AiTextureGetResolutionFunc.argtypes = [AtString, POINTER(c_uint), POINTER(c_uint)]
AiTextureGetResolutionFunc.restype = c_bool

def AiTextureGetResolution(filename):
    width = c_uint(0)
    height = c_uint(0)
    success = AiTextureGetResolutionFunc(filename, width, height)
    return (int(width.value), int(height.value)) if success else None

AiTextureGetNumChannelsFunc = ai.AiTextureGetNumChannels
AiTextureGetNumChannelsFunc.argtypes = [AtString, POINTER(c_uint)]
AiTextureGetNumChannelsFunc.restype = c_bool

def AiTextureGetNumChannels(filename):
    num_channels = c_uint(0)
    success = AiTextureGetNumChannelsFunc(filename, num_channels)
    return int(num_channels.value) if success else None

AiTextureGetChannelNameFunc = ai.AiTextureGetChannelName
AiTextureGetChannelNameFunc.argtypes = [AtString, c_uint]
AiTextureGetChannelNameFunc.restype = AtString

def AiTextureGetChannelName(filename, channel_index):
    return AtStringToStr(AiTextureGetChannelNameFunc(filename, channel_index))

AiTextureGetFormatFunc = ai.AiTextureGetFormat
AiTextureGetFormatFunc.argtypes = [AtString, POINTER(c_uint)]
AiTextureGetFormatFunc.restype = c_bool

def AiTextureGetFormat(filename):
    format = c_uint(0)
    success = AiTextureGetFormatFunc(filename, format)
    return int(format.value) if success else None

AiTextureGetBitDepthFunc = ai.AiTextureGetBitDepth
AiTextureGetBitDepthFunc.argtypes = [AtString, POINTER(c_uint)]
AiTextureGetBitDepthFunc.restype = c_bool

def AiTextureGetBitDepth(filename):
    bit_depth = c_uint(0)
    success = AiTextureGetBitDepthFunc(filename, bit_depth)
    return int(bit_depth.value) if success else None

AiTextureGetMatricesFunc = ai.AiTextureGetMatrices
AiTextureGetMatricesFunc.argtypes = [AtString, POINTER(AtMatrix), POINTER(AtMatrix)]
AiTextureGetMatricesFunc.restype = c_bool

def AiTextureGetMatrices(filename):
    world_to_screen = AtMatrix()
    world_to_camera = AtMatrix()
    success = AiTextureGetMatricesFunc(filename, world_to_screen, world_to_camera)
    return {'world_to_screen': world_to_screen, 'world_to_camera': world_to_camera} if success else None

AiTextureInvalidate = ai.AiTextureInvalidate
AiTextureInvalidate.argtypes = [AtString]
