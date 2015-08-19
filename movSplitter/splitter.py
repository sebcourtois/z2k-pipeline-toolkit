import sys
import re
import os

FPS = 24.0
TC_SEPARATOR = ":"

def convertTcToSecondsTc(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0, in_iSecondsOffset=0, in_iFramesOffset=0):
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

	return hours * 3600 + minutes * 60 + seconds + frames/FPS

def parseEdl(in_sEdlPath):
	f = None
	lines = []
	shots = []

	try:
		f = open(in_sEdlPath, 'r')
		lines =  f.readlines()
	except Exception as e:
		print "Cannot load edl file from " + in_sEdlPath + " : " + str(e)
	finally:
		if f != None:
			f.close()

	if len(lines) == 0:
		print "Can't read edl lines, empty file ?"
		return shots

	tcRegEx = re.compile("(\d{3})\s+GEN\s+V\s+C\s+\d{2}:\d{2}:\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})")
	shotRegEx = re.compile(".*FROM CLIP NAME:  (S\d{3}[a-zA-Z]?)\s(P\d{3})")

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

def splitMovie(in_sSourcePath, in_sEdlPath, in_sSeqFilter=None, in_sSeqOverrideName=None, doSplit=True, exportCsv=True, in_sShotSuffix="0a"):
	dirname, filename = os.path.split(os.path.abspath(__file__))
	batFile = os.path.join(dirname, "split.bat")

	print "splitMovie({0}, {1}, {2}, {3})".format(in_sSourcePath, in_sEdlPath, in_sSeqFilter, in_sSeqOverrideName)

	shots = parseEdl(in_sEdlPath)

	csv = "{0},{1},{2},{3}\n".format('code', 'sg_cut_in', 'sg_cut_out', 'sg_cut_duration')

	for shot in shots:
		if in_sSeqFilter == None or shot["sequence"] == in_sSeqFilter:
			sequenceCode = shot["sequence"].replace("S", "sq") + "0"
			if in_sSeqFilter != None and in_sSeqOverrideName != None:
				sequenceCode = in_sSeqOverrideName

			shotCode = shot["shot"].replace("P", "sh") + in_sShotSuffix

			startseconds = convertTcToSeconds(shot["start"], in_iHoursOffset=-1)
			endseconds = convertTcToSeconds(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1)

			csv += "{0},{1:.0f},{2:.0f},{3:.0f}\n".format(sequenceCode + "_" + shotCode, startseconds * FPS, endseconds * FPS, (endseconds - startseconds) * FPS + 1)

			cmdLine = "{0} {1} {2} {3} {4}".format(batFile, in_sSourcePath, convertTcToSecondsTc(shot["start"], in_iHoursOffset=-1), convertTcToSecondsTc(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1), sequenceCode + "_" + shotCode + "_animatic.mov")

			if doSplit:
				os.system(cmdLine)
			else:
				print cmdLine

	if exportCsv:
		outPath = in_sEdlPath.replace('.edl', '.csv')

		f = None
		try:
			f = open(outPath, 'w')
			f.write(csv)
			f.close()
			print outPath
		except Exception, e:
			pass
		finally:
			if f != None:
				f.close()
	else:
		print csv

if len(sys.argv) < 3:
	print "Two arguments must be given (Source_video_path, edl_path) !"
else:
	args = list(sys.argv)
	print args
	args.pop(0)
	print args
	splitMovie(*args)