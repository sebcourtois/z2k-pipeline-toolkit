import nuke
import nukescripts

#TOGGLE LOCAL OFF
def locOffSelectedStart():
	for selnodesoff in nuke.selectedNodes():
		if selnodesoff.Class() == "Read":
			selnodesoff.knob("localizationPolicy").setValue("off")

