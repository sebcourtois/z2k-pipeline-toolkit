

import os

def getPath(*args, **kwargs):
	return os.path.dirname(__file__)
therootPath = getPath()
