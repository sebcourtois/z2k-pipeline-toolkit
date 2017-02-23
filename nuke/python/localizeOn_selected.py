import nuke
import nukescripts

#TOGGLE LOCAL ON
def locOnSelectedStart():
	for selnodeson in nuke.selectedNodes():
		if selnodeson.Class() == "Read":
			selnodeson.knob("localizationPolicy").setValue("on")