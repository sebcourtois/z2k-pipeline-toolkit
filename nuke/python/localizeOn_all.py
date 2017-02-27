import nuke
import nukescripts

#TOGGLE LOCAL ON
def locOnAllStart():
	for allnodeson in nuke.allNodes():
		if allnodeson.Class() == "Read":
			allnodeson.knob("localizationPolicy").setValue("on")