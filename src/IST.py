import re, time, glob, json, pygame
from pygame.locals import *

class Bunch:
	__init__ = lambda self, **kw: setattr(self, '__dict__', kw)

class IsaacStatTracker:

	def __init__(self, readDelay=60, debug=True):
		#general
		self.readDelay = readDelay
		self.debug = debug
		self.frameCount = 0
		self.seek = 0
		self.isRunOver = False
		self.options = self.loadOptions()
		#isaac
		self.lastCollectedItemID = 0
		self.lastGeneratedDescription = ""
		self.runStartLine = 0
		self.runStartFrame = 0
		self.collectedItems = []
		self.displayedItems = []
		self.displayedImages = []
		self.collectedItemsInfo = []
		self.currentSeed = []
		self.currentRoom = ""
		self.numberOfRoomsEntered = []
		self.runStartFrame = []
		self.bosses = []
		self.lastRun = {}
		#data
		with open('itemsInfo.txt', 'r') as itemsInfoFile:
			self.itemsInfo = json.load(itemsInfoFile)
		self.regex = {
			'newSeed': r'^RNG Start Seed: (.{9})(.+?)$',
			'newClearTime': r'^(Mom clear time: )(\d{1,})$',
			'newPlayer': r'^(Initialized player with )(.{9})( and )(.+?)$',
			'newItem': r'^(Adding collectible )(.{1,3}) (.+?)$',
			'newBoss': r'^(Boss )(\d{1,2})(.+?)$',
			'newMiniBoss': r'(MiniBoss )(\d{1,2})(.+?)$',
			'newPillAction': r'^(Action PillCard Triggered)$',
			'newRoomEntered': r'^(Room )(\S{3,4})'
		}

	def loadOptions(self):
		with open("options.json", "r") as jsonFile:
			options = json.load(jsonFile)
		return options

	def saveOptions(self):
		with open("options.json", "w") as jsonFile:
			json.dump(self.options, jsonFile, indent = 3, sort_keys = True)

	def logMessage(self, msg, level):
		if level=="debug" and self.debug: print msg

	def checkDirectory(self, directoryName):
		import os
		if not os.path.isdir(directoryName):
			os.mkdir(directoryName)

	def saveFile(self, start, end, seed):
		self.checkDirectory("RunLogs")
		timestamp = int(time.time())
		data = "Seed: %s \nRun Data\n %s" % (seed, self.lastRun)
		with open("RunLogs/%s %s.log" % (timestamp, seed), "wb") as runSaveFile:
			runSaveFile.write(data)

	def saveItemText(self, itemID):
		itemIDPadded = str(itemID).zfill(3)
		itemInfo = self.itemsInfo[itemIDPadded]
		itemDescription = self.generateItemDescription(itemInfo)

		if self.lastGeneratedDescription != itemDescription:
			self.lastGeneratedDescription = itemDescription
			try:
				with open('LastItemDescription.txt', 'w') as descriptionSaveFile:
					descriptionSaveFile.write(itemInfo["name"] + itemDescription)
					self.logMessage("Writing Description File...", "debug")
			except Exception:
				self.logMessage("Could not find or open LastItemDescription.txt.", "debug")

		#itemText = font.render("%s%s" % (itemInfo["name"], itemDescription), True, (255, 255, 255))
		#screen.blit(itemText, (2, 2))


	def checkIfEndOfRun(self, line, currentLineNumber):
		if not self.isRunOver:
			diedTo = ""
			endType = ""
			if self.bosses and self.bosses[-1][0] in ['???', 'The Lamb', 'Mega Satan']:
				endType = "Won"
			elif (self.currentSeed != '') and line.startswith('RNG Start Seed:'):
				endType = "Reset"
			elif line.startswith('Game Over.'):
				endType = "Death"
				diedTo = re.search('(?i)Killed by \((.*)\) spawned',line).group(1)
			if endType:
				self.lastRun = {
					"Bosses Defeated: ": self.bosses,
					"Items Collected: ": self.collectedItems,
					"Seed: ": self.currentSeed,
					"Died To: ": diedTo,
					"End Type: ": endType
				}
				self.isRunOver = True
				self.logMessage("End of Run! %s" % self.lastRun, "debug")
				if endType != "Reset":
					self.saveFile(self.runStartLine, currentLineNumber, self.currentSeed)

	def generateItemDescription(self, itemInfo):
		desc = ""
		text = itemInfo.get("text")
		dmg = itemInfo.get("dmg")
		dmgx = itemInfo.get("dmgx")
		delay = itemInfo.get("delay")
		delayx = itemInfo.get("delayx")
		health = itemInfo.get("health")
		speed = itemInfo.get("speed")
		shotspeed = itemInfo.get("shotspeed")
		tearrange = itemInfo.get("range")
		height = itemInfo.get("height")
		tears = itemInfo.get("tears")
		soulhearts = itemInfo.get("soulhearts")
		sinhearts = itemInfo.get("sinhearts")
		if dmg:
			desc += dmg + " dmg, "
		if dmgx:
			desc += "x" + dmgx + " dmg, "
		if tears:
			desc += tears + " tears, "
		if delay:
			desc += delay + " tear delay, "
		if delayx:
			desc += "x" + delayx + " tear delay, "
		if shotspeed:
			desc += shotspeed + " shotspeed, "
		if tearrange:
			desc += tearrange + " range, "
		if height:
			desc += height + " height, "
		if speed:
			desc += speed + " speed, "
		if health:
			desc += health + " health, "
		if soulhearts:
			desc += soulhearts + " soul hearts, "
		if sinhearts:
			desc += sinhearts + " sin hearts, "
		if text:
			desc += text
		if desc.endswith(", "):
			desc = desc[:-2]
		if len(desc) > 0:
			desc = ": " + desc
		return desc

	def clearData(self, screen):
		self.lastCollectedItemID = 0
		self.lastGeneratedDescription = ""
		self.collectedItems = []
		self.bosses = []
		self.roomsEntered = 0
		self.displayedItems = []
		self.displayedImages = []
		screen.fill((0, 241, 15))
		self.logMessage("Cleared Data", "debug")

	def go(self):

		pygame.init()
		pygame.display.set_caption("Isaac Stat Tracker")
		screen = pygame.display.set_mode((self.options["windowWidth"], self.options["windowHeight"]), RESIZABLE)
		screen.fill((0, 241, 15))
		clock = pygame.time.Clock()
		running = True

		while running:
			#Handle PyGame Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.VIDEORESIZE:
					screen = pygame.display.set_mode(event.dict['size'], RESIZABLE)
					screen.fill((0, 241, 15))
					self.options["windowWidth"] = event.dict["w"]
					self.options["windowHeight"] = event.dict["h"]
					self.saveOptions()
					pygame.display.flip()

			pygame.display.flip()
			clock.tick(60)

			if (len(self.collectedItems)) > 0:
				for item in self.collectedItems:
					if item not in self.displayedItems:
						try:
							image = pygame.image.load('ISTData/images/items/%s.png' % item)
							image = pygame.transform.scale(image, (64, 64))
							self.displayedItems.append(item)
							self.displayedImages.append(image)
						except Exception:
							self.logMessage("Error opening file.", "debug")
						
			i,j = 0,0
			if self.displayedImages:
				for item in self.displayedImages:
					screen.blit(item, (i, j))

					i += 64
					if i > self.options["windowWidth"]:
						i = 0
						j += 64


			self.frameCount += 1

			if self.frameCount % self.readDelay == 0:
				if self.lastCollectedItemID:
					self.saveItemText(self.lastCollectedItemID)

				content = ""
				try:
					with open('../log.txt', 'r') as logFile:
						content = logFile.read()
				except Exception:
					self.logMessage("log.txt is not found, is the IsaacStatTracker folder in 'My Games/Binding of Isaac Rebirth'?", "debug")

				self.splitfile = content.splitlines()

				for currentLineNumber, line in enumerate(self.splitfile[self.seek:]):
					if line.startswith('Mom clear time:'):
						killTime = re.match(self.regex["newClearTime"], line, re.M)

					self.checkIfEndOfRun(line, currentLineNumber + self.seek)
					
					if line.startswith('RNG Start Seed:'):
						self.currentSeed = re.match(self.regex["newSeed"], line, re.M).group(1)
						self.logMessage("-----------------\nStarting a new run, seed: %s" % self.currentSeed, "debug")
						self.run_start_frame = self.frameCount
						self.clearData(screen)
						self.runStartLine = currentLineNumber + self.seek
						self.isRunOver = False

					if line.startswith('Room'):
						self.currentRoom = re.match('^(Room )(\d{1,}.\d{1,})\((.*)\)$', line, re.M).group(3)
						self.numberOfRoomsEntered += 1
						self.logMessage("Entered room: %s" % self.currentRoom, "debug")

					if line.startswith('Adding collectible'):
						itemID = re.match(self.regex['newItem'], line, re.M).group(2)
						itemIDPadded = itemID.zfill(3)

						if not itemID in self.collectedItems:
							itemInfo = self.itemsInfo[itemIDPadded]
							self.collectedItems.append(itemID)
							self.lastCollectedItemID = itemID
							self.logMessage("Padded ID %s" % itemIDPadded, "debug")
							self.logMessage("Picked up item. ID: %s Name: %s" % (itemID, itemInfo["name"]), "debug")
						else:
							self.logMessage("Skipped adding item %s to avoid space-bar duplicates" % itemID, "debug")

				self.seek = len(self.splitfile)


ist = IsaacStatTracker()
ist.go()