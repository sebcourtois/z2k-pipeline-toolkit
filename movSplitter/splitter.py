import sys
import re
import os
import subprocess

SHOT_FOLDER = "\\\\Zombiwalk\\Projects\\zomb\\shot\\"
SHOT_TEMPLATE = "{sequence}\\{sequence}_{shot}\\00_data"

FPS = 24.0
TC_SEPARATOR = ":"

def getShotFolder(in_sSequence, in_sShot):
	return SHOT_FOLDER + SHOT_TEMPLATE.format(sequence=in_sSequence, shot=in_sShot)

def convertTcToSecondsTc(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0, in_iSecondsOffset=0, in_iFramesOffset=0):
	hours, minutes, seconds, frames = [int(val) for val in in_Tc.split(TC_SEPARATOR)]

	frames += in_iFramesOffset
	if frames < 0:
		frames += FPS
		in_iSecondsOffset -= 1
	elif frames >= FPS:
		frames -= FPS
		in_iSecondsOffset += 1

	seconds += in_iSecondsOffset
	if seconds < 0:
		seconds += 60
		in_iMinutesOffset -= 1
	elif seconds >= 60:
		seconds -= 60
		in_iMinutesOffset += 1

	minutes += in_iMinutesOffset
	if minutes < 0:
		minutes += 60
		in_iHoursOffset -= 1
	elif minutes >= 60:
		minutes -= 60
		in_iHoursOffset += 1

	hours += in_iHoursOffset

	#print "{0} {1} {2} {3}".format(hours, minutes, seconds, frames)

	return "{1}{0}{2}{0}{3}".format(TC_SEPARATOR, hours, minutes, seconds + frames / FPS)

def convertTcToSeconds(in_Tc, in_fps=FPS, in_iHoursOffset=0, in_iMinutesOffset=0, in_iSecondsOffset=0, in_iFramesOffset=0):
	hours, minutes, seconds, frames = [int(val) for val in in_Tc.split(TC_SEPARATOR)]

	frames += in_iFramesOffset
	if frames < 0:
		frames += FPS
		in_iSecondsOffset -= 1
	elif frames >= FPS:
		frames -= FPS
		in_iSecondsOffset += 1

	seconds += in_iSecondsOffset
	if seconds < 0:
		seconds += 60
		in_iMinutesOffset -= 1
	elif seconds >= 60:
		seconds -= 60
		in_iMinutesOffset += 1

	minutes += in_iMinutesOffset
	if minutes < 0:
		minutes += 60
		in_iHoursOffset -= 1
	elif minutes >= 60:
		minutes -= 60
		in_iHoursOffset += 1

	hours += in_iHoursOffset

	return hours * 3600 + minutes * 60 + seconds + frames / FPS

def parseEdl(in_sEdlPath, in_sSeqFilter=None):
	f = None
	lines = []
	shots = []

	try:
		f = open(in_sEdlPath, 'r')
		lines = f.readlines()
	except Exception as e:
		print "Cannot load edl file from " + in_sEdlPath + " : " + str(e)
	finally:
		if f != None:
			f.close()

	if len(lines) == 0:
		print "Can't read edl lines, empty file ?"
		return shots

	tcRegEx = re.compile("(\d{3})\s+GEN\s+V\s+C\s+\d{2}:\d{2}:\d{2}:\d{2}\s+\d{2}:\d{2}:\d{2}:\d{2}\s+(\d{2}:\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2}:\d{2})")
	shotRegEx = re.compile(".*FROM CLIP NAME:  (SQ\d{4}[a-zA-Z]?)\s\s(P\d{4}[a-zA-Z]?)")
	seqRegEx = re.compile(".*FROM CLIP NAME:  (SQ\d{4}[a-zA-Z]?)")


	fileLength = len(lines)

	for counter in range(fileLength):
		matchObj = tcRegEx.match(lines[counter])
		if matchObj:
			shotMatchObj = shotRegEx.match(lines[counter + 1])

			if shotMatchObj:
				shots.append({
							"index":matchObj.group(1).strip(),
							"sequence":shotMatchObj.group(1).strip(),
							"shot":shotMatchObj.group(2).strip(),
							"start":matchObj.group(2).strip(),
							"end":matchObj.group(3).strip()
							})
			else:
				seqMatchObj = seqRegEx.match(lines[counter + 1])
				if seqMatchObj:
					shots.append({
								"index":matchObj.group(1).strip(),
								"sequence":seqMatchObj.group(1).strip(),
								"shot":'P0000A',
								"start":matchObj.group(2).strip(),
								"end":matchObj.group(3).strip()
								})
				else:
					print ("Error reading shot info for line {0} ({1})"
							.format(counter, lines[counter + 1].replace('\n', '')))
					return None
	return shots

def splitMovie(in_sSourcePath, in_sEdlPath, in_sSeqFilter=None, in_sSeqOverrideName=None,
				doSplit=True, exportCsv=True, in_sShotSuffix="", in_bExportInShotFolders=True):
	dirname, filename = os.path.split(os.path.abspath(__file__))
	batFile = os.path.join(dirname, "split.bat")

	print "splitMovie({0}, {1}, {2}, {3})".format(in_sSourcePath, in_sEdlPath, in_sSeqFilter, in_sSeqOverrideName)

	shots = parseEdl(in_sEdlPath)

	if shots is None:
		print "Cannot read Edl correctly (see above) !"
		return

	csv = ("{0},{1},{2},{3},{4},{5}\n".format('Shot Code', 'Cut In', 'Cut Out',
												'Cut Duration', 'Scn In', 'Scn Out'))

	lenShots = len(shots)
	counter = 1
	for shot in shots:
		sequenceCode = shot["sequence"].replace("SQ", "sq")
		shotCode = shot["shot"].replace("P", "sh").replace("A", "a") + in_sShotSuffix
		startseconds = convertTcToSeconds(shot["start"], in_iHoursOffset=-1)
		endseconds = convertTcToSeconds(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=-1)
		if in_sSeqFilter == None or shot["sequence"] == in_sSeqFilter:

			if in_sSeqFilter != None and in_sSeqOverrideName != None:
				sequenceCode = in_sSeqOverrideName

			fmtFields = (batFile, '{0}'.format(in_sSourcePath),
						convertTcToSecondsTc(shot["start"], in_iHoursOffset=-1),
						convertTcToSecondsTc(shot["end"], in_iHoursOffset=-1, in_iFramesOffset=0),
						sequenceCode + "_" + shotCode + "_animatic.mov")
			cmdLine = "{0} {1} {2} {3} {4}".format(*fmtFields)

			if in_bExportInShotFolders:
				path = getShotFolder(sequenceCode, shotCode)
				if not os.path.isdir(path):
					os.makedirs(path)
				cmdLine += " {0}\\".format(path)

			if doSplit:
				os.system(cmdLine)
			else:
				print cmdLine

			percent = counter * 100 / lenShots
			bar = ["-" for n in range(int(percent * .5))]
			print ("\nShot {0:04d}/{1:04d} {2:.0f}% |{3:<50}|"
					.format(counter, lenShots, percent, "".join(bar)))
			counter += 1

		fmtFields = (sequenceCode + "_" + shotCode, startseconds * FPS,
					endseconds * FPS,
					(endseconds - startseconds) * FPS + 1,
					101,
					101 + (endseconds - startseconds) * FPS)
		csv += "{0},{1:.0f},{2:.0f},{3:.0f},{4:.0f},{5:.0f}\n".format(*fmtFields)
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
	args.pop(0)
	print "splitMovie" + ",".join(args)
	splitMovie(*args)
