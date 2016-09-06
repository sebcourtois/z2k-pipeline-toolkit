#! /usr/bin/python

print "yahoo"
import jipe_ViewContact_Tool_v002 as vct
reload(vct)
ViewportSwitch_UI_I = vct.ViewportSwitch_UI()
ViewportSwitch_UI_I.createWindow()