import sys
import re
import os

FPS = 24.0
TC_SEPARATOR = ":"

def convertTcToSeconds(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0, in_iSecondsOffset=0, in_iFramesOffset=0):
	hours, minutes, seconds, frames = [int(val) for val in in_Tc.split(TC_SEPARATOR)]

	frames += in_iFramesOffset
	if frames < 0:
		frames +=  FPS
		in_iSecondsOffset -= 1
	elif frames >= FPS:
		frames -= FPS
		in_iSecondsOffset += 1

	seconds += in_iSecondsOffset
	if seconds < 0:
		seconds +=  60
		in_iMinutesOffset -= 1
	elif seconds >= 60:
		seconds -= 60
		in_iMinutesOffset += 1

	minutes += in_iMinutesOffset
	if minutes < 0:
		minutes +=  60
		in_iHoursOffset -= 1
	elif minutes >= 60:
		minutes -= 60
		in_iHoursOffset += 1

	hours += in_iHoursOffset

	#print "{0} {1} {2} {3}".format(hours, minutes, seconds, frames)

	return "{1}{0}{2}{0}{3:.2f}".format(TC_SEPARATOR, hours, minutes, seconds + frames/FPS)

def parseEdl(in_sEdlPath):
	f = None
	lines = []
	shots = []

	try:
		f = open(in_sEdlPath, 'r')
		lines =  f.readlines()
	except Exception as e:
		pc.warning("Cannot load edl file from " + in_sEdlPath + " : " + str(e))
	finally:
		if f != None:
			f.close()

	if len(lines) == 0:
		print "Can't read edl lines, empty file ?"
		return shots

	tcRegEx = re.compile("(\d{3})\s+GEN\s+V\s+C\s+\d{2}:\d{2}:\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})")
	shotRegEx = re.compile(".*FROM CLIP NAME:  (S\d{3})\s(P\d{3})")

	fileLength = len(lines)

	for counter in range(fileLength):
		matchObj = tcRegEx.match(lines[counter])
		if matchObj:
			shotMatchObj = shotRegEx.match(lines[counter+1])
			if shotMatchObj:
				shots.append({"index":matchObj.group(1).strip(), "sequence":shotMatchObj.group(1).strip(), "shot":shotMatchObj.group(2).strip(), "start":matchObj.group(2).strip(), "end":matchObj.group(3).strip()})
			else:
				print "Error reading shot info for line {0} ({1})".format(counter, lines[counter+1])

	return shots

def splitMovie(in_sSourcePath, in_sEdlPath):
	dirname, filename = os.path.split(os.path.abspath(__file__))
	batFile = os.path.join(dirname, "split.bat")

	print "splitMovie({0}, {1})".format(in_sSourcePath, in_sEdlPath)

	shots = parseEdl(in_sEdlPath)

	for shot in shots:
		cmdLine = "{0} {1} {2} {3} {4}".format(batFile, in_sSourcePath, convertTcToSeconds(shot["start"], in_iHoursOffset=-1), convertTcToSeconds(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1), shot["sequence"] + "_" + shot["shot"] + ".mov")
		#print cmdLine
		os.system(cmdLine)

if len(sys.argv) != 3:
	print "Two arguments must be given (Source_video_path, edl_path) !"
else:
	splitMovie(sys.argv[1], sys.argv[2])