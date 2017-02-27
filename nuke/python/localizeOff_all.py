import nuke
import nukescripts

#TOGGLE LOCAL OFF
def locOffAllStart():
	for allnodesoff in nuke.allNodes():
		if allnodesoff.Class() == "Read":
			allnodesoff.knob("localizationPolicy").setValue("off")

