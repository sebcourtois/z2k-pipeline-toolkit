# import   constant
import dminutes.Z2K_ReleaseTool.modules as ini
reload(ini)
from dminutes.Z2K_ReleaseTool.modules import *
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_CHAR_checks as Z2K_PcheckD
reload(Z2K_PcheckD)


Z2K_Pcheck = Z2K_PcheckD.checkModule(GUI=False,debugFile =DEBUGFILE_PREVIZ_CHR)
result = Z2K_Pcheck.btn_cleanAll()