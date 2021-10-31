# Subtitle Translation
# requires googletrans and pysub-parser

# for language code, please view https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages1
# or run "sudo pip3 install pysub-parser googletrans==4.0.0rc1" before starting this script
# due to some weird bugs in googletrans stable build, using the release candidate builds are even more stable than the stable build itself

# subTranslate
# how it works:
# method 1 (default): parse subtitle --> send to google to translate --> generate a new subtitle file
# method 2: parse subtitle --> send to google to translate --> duplicate original subtitle file --> find and replace text
#
# how does "parse subtitle" works:
# this script uses pysubparser as an easy solution for reading subtitles. This script will then take advantage of the ability of reading start and end timings to generate a new subtitle file
#
# how does "send to google to translate" works:
# this script uses the google translate API for translation. As such, it is common that google will block any suspicious connections to google API.
# as a counter, this script will attempt to send short burst of requests every few seconds, which in theory will look less like a DDOS attack to google
# however, this function will mean that the script will be alot more slower (up to 300% slower), but will ensure full functionality in the long run
# if you choose to risk getting ip ban by google, you maybe set "segments = 0" down below, which will send all the lines to google quickly without mercy
#
# how does preserveOriginalCodec works:
# base on your input subtitle, the script will generate a new file with the same codec as the input subtitle. however, special edits done to the subtitle will be gone.
# to preserve the original edits, set preserveOriginalEdits = 1, which will use method 2 instead

import platform
import os
from os import system, name # clearScreen
from pathlib import Path
from os import listdir
from os.path import isfile, join
import subprocess
import shutil
import re
import datetime
import time
import sys
import glob
import re
import random
import string
import shutil
from pysubparser import parser
from googletrans import Translator

arrayOfExtentions = [".ass", ".srt"] # which file extension to search for
identifyingCharacteristic = ".english.default" # define what the input should have in their name. Leave empty for none
extraIdentifyingCharacteristic = ".translated" # creatings a marking characteristic in the output file. Leave empty for none
cwd = os.getcwd() # sets current location. Specify a specific location if you like
language = "zh-cn"
sleep_duration = 2 # sleeps between each intervals to avoid being banned. Recommend = 10
illegalList = ["-", ">", ":", " "] # will remove such characters in lines. This function will not be enabled if preserveOriginalEdits is disabled
preserveOriginalEdits = 0 # by default, this script will write a clean new srt file. But if you want the script to use the original file as a base, then this script will try to preserve it.
#                           but this function has an issue where it will skip some lines due to how python works. It is recommended that you leave this to 0
#
preserveOriginalCodec = 1 # by default, this value will be 1. if the subtitle codec is supported, tihis script will attempt to create a new subtitle with the original codec.
#                           if disabled, the script will always generate a srt file regardless of the input.
#                           but please note that this function only matters if preserveOriginalEdits is disabled
#
# segments ==
# segments seperates the subtitles into smaller chuncks, this enables the script to delay between chunks to avoid ip ban
# so if you set segments = 20, the script wlill send 20 requests to google API in a rapid succession. 
# and so if you disable segments, script will send all of the requests immediately without any concerns for waiting
# specifying a higher value will be equal to higher risk of ban
# if you meet any issues, you can try specifying a smaller chunk
# set to 0 to disable segments [not recommended]
# recommended = 5
segments = 20

for x in range(100):
	illegalList.append(x)

def findFiles(arrayOfNames, workingDir): # file files in a given directory
	filtered = []
	for extension in arrayOfNames:
		path = cwd
		files = []
		for r, d, f in os.walk(path):
			for file in f:
				if extension in file:
					files.append(os.path.join(r, file))
		filtered.append(list(filter(lambda k: extension in k, files)))
		combinedFiltered = combineArray(filtered)
	return combinedFiltered

def combineArray(inputx): # converts two dimension array to one dimension
	combine = []
	for x in inputx:
		for y in x:
			combine.append(y)
	return combine

def timeConvert(seconds):
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return "%d:%02d:%02d" % (hour, minutes, seconds)

def parseSubtitles(inputx):
	# parse the subtitles into a variable
	subtitles = parser.parse(inputx)
	return subtitles

def rapidTranslate(inputx, languagey):
	# quickly burst through list to google translateAPI
	translator = Translator()
	results = []
	for x in inputx:
		results.append(translator.translate(x, dest=languagey))
		time.sleep(0.2)
	return results

def translateSubtitles(inputVariable, languagex):
	global sleep_duration, segments
	# translate the variable and return a variable
	# NOTE: Please understand that this might not work since google might limit their API
	inputVariablex = []
	for x in inputVariable:
		inputVariablex.append(str(x.text))
	inputVariable = inputVariablex
	translator = Translator()
	translated = []
	print("attempting conversion, this might take awhile..")
	print("target language:", languagex)
	print("total lines:", len(inputVariable))
	if segments > 0:
		seperatedList = split_list(inputVariable, int(len(inputVariable) / segments))
		print("total segments:", len(seperatedList))
		print("total lines in each segments:", segments)
		if segments > 50:
			print("[WARNING] segments is greater than 50, which risks the chances of an IP ban")
			print("[WARNING] you can ignore this warning if you know what you are doing")
	else:
		seperatedList = []
		seperatedList.append(inputVariable)
		print("")
		print("[WARNING] script is attempting to send the full", len(inputVariable), "lines to the google API")
		print("[WARNING] this is not recommended as it might create an issue with the chunk being too big to process")
		print("[WARNING] set segments to something higher than 0 to avoid this issue")
		print("[WARNING] this script might look unresponsive for a long time")
	if sleep_duration < 2:
		print("")
		print("[WARNING] sleep_duration is less than 2, which risks the chances of an IP ban")
		print("[WARNING] you can ignore this warning if you know what you are doing")
	elif segments > 0:
		print("sleep between translations:", sleep_duration, "seconds")
	count = 0
	while True:
		try:
			translated = []
			for x in seperatedList:
				timeStart = time.time()
				result = rapidTranslate(x, languagex)
				for x in result:
					translated.append(str(x.text))
				count = count + 1
				timeTaken = time.time() - timeStart
				timeLeft = ((len(seperatedList) - count) * timeTaken) + ((len(seperatedList) - count) * sleep_duration)
				percentageCompleted = (count/len(seperatedList)) * 100
				if int(percentageCompleted) == 100:
					print("progress:", int(percentageCompleted), "percent completed. Estimated time left to completion (hh:mm:ss):", timeConvert(int(timeLeft)))
					print("translation process has been completed")
				else:
					print("progress:", int(percentageCompleted), "percent completed. Estimated time left to completion (hh:mm:ss):", timeConvert(int(timeLeft)), end="\r")
				time.sleep(sleep_duration)
			return translated
		except OSError as error:
			print(error)
			print("")
			print("[WARNING] API failure? Retrying in 5 minutes")
			if not segments > 0:
				print("[WARNING] detected that segments is not enabled. please consider enabling it instead and try again")
			else:
				print("[WARNING] script thinks that its a possible IP ban issue")
			print("[NOTE] ctrl + c again to exit")
			time.sleep(300)
			print("[RETRY] wait time passed. trying again now..")


def copyAndEditSub(inputx, inputBase, inputVariable):
	global identifyingCharacteristic, language, extraIdentifyingCharacteristic, illegalList
	# copy the original file, then find and replace the specific texts accordingly
	# this will preserve the original edits done to the subtitles.
	final = target.replace(identifyingCharacteristic, "." + language + extraIdentifyingCharacteristic)
	shutil.copyfile(target, final) # duplicate original file to a new file
	inputVariable = list(inputVariable)
	inputBase = list(inputBase)
	# clean up the parse content
	for x in range(len(inputBase)):
		print(type(inputBase[x]))
		var = str(inputBase[x])
		replacementText = str(x) + " > "
		inputBase[x] = var.replace(replacementText, "")
	# remove illegal characters
	for x in range(len(inputBase)):
		for y in illegalList:
			if inputBase[x] == y:
				inputBase[x] = ""
				inputVariable[x] = ""
	for x in range(len(inputBase)):
		print(str(inputBase[x]), " --> ", str(inputVariable[x]))
	for x in range(len(inputVariable)):
		reading_file = open(final, "r")
		new_file_content = ""
		for line in reading_file:
			stripped_line = line.strip()
			new_line = stripped_line.replace(str(inputBase[x]), str(inputVariable[x]))
			new_file_content += new_line +"\n"
		reading_file.close()
		writing_file = open(final, "w")
		writing_file.write(new_file_content)
		writing_file.close()
	print("wrote translation into", final)
	print("please note that this method has an issue of being unable to properly replace lines with a line break.")
	print("this issue has been solved by actually generating a new srt file. however, this method will not preserve existing edits.")

def writeNewSubtitle(inputx, inputBase, inputVariable):
	# this function will write a new srt file instead of reusing the old one
	global identifyingCharacteristic, language, extraIdentifyingCharacteristic, arrayOfExtentions
	print("writing new srt file")
	final = target.replace(identifyingCharacteristic, "." + language + extraIdentifyingCharacteristic)
	subStartTime = []
	subEndTime = []
	if ".ass" in inputx and preserveOriginalCodec == 1:
		# ass file support
		for x in inputBase:
			# the reason for removing 000 in time code is because i have no idea why subparse keep adding 000 at the bad
			# this is like a quick patch and hoping it wont cause any issue in the future
			subStartTime.append(str(x.start).replace("000", ""))
			subEndTime.append(str(x.end).replace("000", ""))
		f = open(final, "w+")
		f.write(str("[Script Info]\n"))
		f.write(str("; script generated and translated by subTranslate.py\n"))
		f.write(str("WrapStyle: 1\n"))
		f.write(str("\n"))
		f.write(str("[Events]\n"))
		f.write(str("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"))
		for x in range(len(inputVariable)):
			f.write(str("Dialogue: 0,"))
			f.write(str(subStartTime[x] + "," + subEndTime[x]))
			f.write(str(",Default,,0000,0000,0000,,"))
			f.write(str(inputVariable[x]) + "\n")
		f.close()

	else:
		# srt file support or converts anything unknown to srt anyways
		for x in inputBase:
			# the reason for removing 000 in time code is because i have no idea why subparse keep adding 000 at the bad
			# this is like a quick patch and hoping it wont cause any issue in the future
			subStartTime.append(str(x.start).replace("000", ""))
			subEndTime.append(str(x.end).replace("000", ""))
		for x in arrayOfExtentions:
			if x in final:
				final = final.replace(x, ".srt")
		f  = open(final, "w+")
		f.write(str("1\n"))
		f.write(str("00:00:00.000 --> 00:00:00.000\n"))
		f.write(str("script generated and translated by subTranslate.py\n"))
		f.write("\n")
		for x in range(len(inputVariable)):
			f.write(str(x+2) + "\n")
			f.write(subStartTime[x] + " --> " + subEndTime[x] + "\n")
			f.write(str(inputVariable[x]) + "\n")
			f.write("\n")
		f.close()
	print("finished writing subtitle into", final)


def split_list(alist, wanted_parts):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]


targetFiles = findFiles(arrayOfExtentions, cwd) # search for targets
print("job started")
for x in targetFiles:
	print(x)
if not identifyingCharacteristic == "":
	print("only files with", identifyingCharacteristic, "will be processed. you may safely ignore the rest.")
for target in targetFiles: # recursive scrap thru all files in searched list
	for extension in arrayOfExtentions: # helps with determining the extension
		if not target.count(extension) == 0: # prevent works on external
			if identifyingCharacteristic in target:
				if not extraIdentifyingCharacteristic in target:
					if not os.path.isfile(target.replace(identifyingCharacteristic, extraIdentifyingCharacteristic)):
						targetConverted = target.replace(identifyingCharacteristic, "." + language + ".translated")
						if not os.path.isfile(targetConverted):
							if not "._" in target:
								TotalTimeStart = time.time()
								print("")
								print("processing", target)
								if preserveOriginalEdits == 1:
									print("[WARNING] preserveOriginalEdits has been enabled. this function will work terribily with frames that has more than 1 lines")
									print("[WARNING] to avoid facing this issue, disable preserveOriginalEdits")
									try:
										copyAndEditSub(target, parseSubtitles(target), translateSubtitles(parseSubtitles(target), language))
									except:
										print("[WARNING] failed to convert", target)
								else:
									try:
										writeNewSubtitle(target, parseSubtitles(target), translateSubtitles(parseSubtitles(target), language))
									except:
										print("[WARNING] failed to convert", target)
								TotalTimeTaken = time.time() - TotalTimeStart
								print("Time taken for this subtitle (hh:mm:ss):", timeConvert(int(TotalTimeTaken)))

print("job done")
