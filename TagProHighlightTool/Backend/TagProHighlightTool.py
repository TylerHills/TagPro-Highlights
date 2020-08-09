import bs4
from urllib.request import urlopen
import re
from pytube import YouTube
from moviepy.editor import *
from datetime import datetime
import os
import requests
import shutil

class HighlightTool:
	gameLabels = ["G1H1", "G1H2", "G2H1", "G2H2", "G3H1", "G3H2"]
	
	def __init__(self, youtubeLink_, tagproEUs_, halfStartTimes_):
		self.youtubeLink = youtubeLink_
		self.tagproEUs = tagproEUs_
		self.halfStartTimes = halfStartTimes_
		
		self.outputFolder = ""
		self.highlightFileList = []
		self.streamableShortcodes = []
		self.status = ""
		
		self.streamableAccount = "tylerhills1986+tph@gmail.com"
		self.streamablePassword = "highlights"
		
		self.caps = []
		
	def run(self):
		self.downloadYoutubeVideo(self.youtubeLink)
		self.parseEU(self.tagproEUs)
		self.orderCaps()
		self.display()
		self.createHighlightFiles()
		self.uploadHighlightFiles()
		shutil.rmtree(self.outputFolder)
		self.status = "Finished"
		
	def display(self):
		print()
		print("Youtube - " + self.youtubeLink)
		print()
		for capList in self.caps:
			print(self.gameLabels[capList[0].game])
			for cap in capList: cap.display()
	
	def orderCaps(self):
		self.status = "Finalizing cap data"
		for capList in self.caps:
			capList.sort(key=lambda x: x.grabTime)
							
	def remove_values_from_list(self, the_list, val):
		return [value for value in the_list if value != val]
	
	def parseEU(self, tagProEUs):
		print("Parsing EUs")
		gameCounter = 0		# keeps track of halves
		self.status = "Parsing EUs" + str(gameCounter + 1) + "/" + str(len(self.tagproEUs))
		
		for tagProEU in tagProEUs:
			page = urlopen(tagProEU)
			soup = bs4.BeautifulSoup(page, "html.parser")

			# get all the attacks table data
			table = soup.find("table", "scoreboard attacks")
			table_body = table.find('tbody')
			data = []
			rows = table_body.find_all('tr')

			for row in rows:
				cols = row.find_all('td')
				cols = [ele.text.strip() for ele in cols]
				data.append([ele for ele in cols if ele])

			# get just cap data
			totalCaptures = len([i for i, s in enumerate(data) if 'Capture' in s]) # number of caps

			capData = []
			for row in data[:(totalCaptures)]:
				for cell in row:
					cellText = cell.strip('✓')
					capData.append(cellText.strip(' '))
					if cellText == "Capture": break		# stops parsing after "Capture" (excludes pup data)

			# clean up pup data, leaves only what we need
			capData = self.remove_values_from_list(capData, "0")
			capData = self.remove_values_from_list(capData, "0:00.00")
			capData = self.remove_values_from_list(capData, "Capture")

			# create Capture objects
			gameCaps = []
			for i in range(0, len(capData), 3):
				gameCaps.append(Capture(gameCounter, capData[i], capData[i + 2], capData[i + 1]))
				
			self.caps.append(gameCaps)	
			print(self.gameLabels[gameCounter] + " processed")
			gameCounter += 1
			
	def downloadYoutubeVideo(self, ytLink):
		self.status = "Fetching Youtube video"
		print("Downloading Youtube...")
		
		yt = YouTube(ytLink)
		self.outputFolder = "./fileGeneration/" + yt.title.replace(' ', '') + datetime.now().strftime("%d%m%y%H%M%S/")
		os.mkdir(self.outputFolder)
				
		for attempt in range(7):
			try:
				yt.streams.order_by('resolution').desc()[attempt].download(output_path = self.outputFolder, filename = "source")
			except:
				continue
			else:
				break

		print("Download finished")
	
	def createHighlightFiles(self):
		print("Creating Highlight Clips")
		self.status = "Creating Highlight Clips"
		for capList in self.caps:
			capCount = 1
			for cap in capList:
				clipLabel = self.gameLabels[cap.game] + " - " + cap.player + " - " + "cap" + str(capCount)
				start = self.getTotalSeconds([self.halfStartTimes[cap.game], cap.grabTime]) - 5
				finish = self.getTotalSeconds([self.halfStartTimes[cap.game], cap.grabTime, cap.holdDuration]) + 3
				self.writeVideoFile(cap.player, clipLabel, start, finish)
				capCount += 1
	
	def writeVideoFile(self, ballName, clipFileName, startClip, finishClip):
		#print(ballName + " - " + clipFileName + " - " + str(startClip) + " - " + str(finishClip))
		txt_clip = (TextClip(ballName, fontsize = 22, color = 'white')
             .set_position('bottom')
             .set_duration(10))
			 
		#(start time + grab time - 5), start time + grab time + hold duration + 3
		video = VideoFileClip(self.outputFolder + "/source.mp4").subclip(startClip, finishClip) 
		result = CompositeVideoClip([video, txt_clip])
		result.write_videofile(self.outputFolder + "/" + clipFileName + ".mp4", fps = 60)
		video.close()
		result.close()
	
	def getTotalSeconds(self, times):
		seconds = 0
		for time in times:
			seconds += self.timeStrToSeconds(time)
		return seconds
			
	def timeStrToSeconds(self, time_str):
		# strip milliseconds and split mins and seconds
		m, s = time_str.split('.', 1)[0].split(':')
		seconds = int(m) * 60 + int(s)
		return seconds
	
	def uploadHighlightFiles(self): 
		self.status = "Uploading highlights to Streamable"
		files = [f for f in os.listdir(self.outputFolder) if f != "source.mp4"]
		for f in files:
			self.streamableShortcodes.append(self.uploadToStreamable(f))
	
	def uploadToStreamable(self, file):
		url = "https://api.streamable.com/upload"
		vid_file = {'file': open(self.outputFolder + file, 'rb')}
		resp = requests.post(url, files=vid_file, auth=(self.streamableAccount, self.streamablePassword), data={'title': file})
		return resp.json()['shortcode']
		
		url = "https://api.streamable.com/upload"
		file = "./fileGeneration/NLTPS16W6DNOvsREV080820001236/G1H1 - Bjird - cap4.mp4"
		vid_file = {'file': open(file, 'rb')}
		resp = requests.post(url, files=vid_file, auth=(acct, pas), data={'title': "G1H1 - Bjird - cap1"})
		return resp.json()['shortcode']
		
	def displayLinks(self):
		for shortcode in self.streamableShortcodes:
			print("http://streamable.com/" + shortcode)

	def test(self):
		test = 1
		
class Capture:
	def __init__(self, game_, grabTime_, holdDuration_, player_):
		self.game = game_
		self.grabTime = grabTime_
		self.holdDuration = holdDuration_
		self.endTime = ""
		self.player = player_
		#self.team = team_
		
	def display(self):
		if len(self.player) > 6:
			print("Player - " + self.player + "\tGrab time - " + self.grabTime + "\tHold duration - " + self.holdDuration)
		else: # formatting
			print("Player - " + self.player + "\t\tGrab time - " + self.grabTime + "\tHold duration - " + self.holdDuration)
		
###########################################################################################################################	

yt = "https://www.youtube.com/watch?v=TJn14fIaeck"
EUs = ["https://tagpro.eu/?match=2318215"]
halfStarts = ["0:10"]
#EUs = ["https://tagpro.eu/?match=2318215", "https://tagpro.eu/?match=2318235", "https://tagpro.eu/?match=2318265", "https://tagpro.eu/?match=2318280"]
#halfStarts = ["0:10", "16:07", "34:51", "49:52"]

highlights = HighlightTool(yt, EUs, halfStarts)
highlights.run()
#highlights.display()
highlights.displayLinks()



