
import dminutes.Z2K_ReleaseTool.modules.Z2K_Previz_SET_checks as Z2K_PcheckD
reload(Z2K_PcheckD)


Z2K_Pcheck = Z2K_PcheckD.checkModule(GUI=False)
result = Z2K_Pcheck.btn_cleanAll()