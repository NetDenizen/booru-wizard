"Components associated with reading and writing the JSON-based metadata files handled by this software."

import threading
import os.path
from enum import Enum
import json

import wx
from pubsub import pub

from booruwizard.lib.tag import TagsContainer

# Image display related values
DEFAULT_MAX_IMAGE_BUFSIZE = 100000000
DEFAULT_IMAGE_QUALITY = wx.IMAGE_QUALITY_HIGH
IMAGE_QUALITY_LOOKUP = {
	'h2+1'    : wx.IMAGE_QUALITY_HIGH,
	'hi2+1'   : wx.IMAGE_QUALITY_HIGH,
	'high2+1' : wx.IMAGE_QUALITY_HIGH,
	'h2'      : wx.IMAGE_QUALITY_BICUBIC,
	'hi2'     : wx.IMAGE_QUALITY_BICUBIC,
	'high2'   : wx.IMAGE_QUALITY_BICUBIC,
	'h1'      : wx.IMAGE_QUALITY_BOX_AVERAGE,
	'hi1'     : wx.IMAGE_QUALITY_BOX_AVERAGE,
	'high1'   : wx.IMAGE_QUALITY_BOX_AVERAGE,
	'm'       : wx.IMAGE_QUALITY_BILINEAR,
	'med'     : wx.IMAGE_QUALITY_BILINEAR,
	'medium'  : wx.IMAGE_QUALITY_BILINEAR,
	'l'       : wx.IMAGE_QUALITY_NEAREST,
	'lo'      : wx.IMAGE_QUALITY_NEAREST,
	'low'     : wx.IMAGE_QUALITY_NEAREST,
}

# Post safety settings
class safety(Enum): #TODO: Change name to rating
	SAFE         = 0
	QUESTIONABLE = 1
	EXPLICIT     = 2

DEFAULT_SAFETY = safety.QUESTIONABLE

#TODO: Case insensitive dict
SAFETY_NAMES_LOOKUP = {
	'safe'         : safety.SAFE,
	'questionable' : safety.QUESTIONABLE,
	'explicit'     : safety.EXPLICIT,
	'Safe'         : safety.SAFE,
	'Questionable' : safety.QUESTIONABLE,
	'Explicit'     : safety.EXPLICIT,
	's'            : safety.SAFE,
	'q'            : safety.QUESTIONABLE,
	'e'            : safety.EXPLICIT,
	'S'            : safety.SAFE,
	'Q'            : safety.QUESTIONABLE,
	'E'            : safety.EXPLICIT
}

SAFETY_VALUES_LOOKUP = {
	safety.SAFE         : 's',
	safety.QUESTIONABLE : 'q',
	safety.EXPLICIT     : 'e'
}

# A single managed file and its exception
class FileOpError(Exception):
	def __init__(self, message, errno, strerror):
		super().__init__( ''.join( (message, ' [errno ', errno, ']: ', strerror) ) )

class ManagedFile:
	def __init__(self, OutputDir, path, IsChangedCallback, DataCallback, ReserveCallback, TimerCallback):
		self.lock = threading.Semaphore(1)
		self.path = ''.join( (os.path.join(OutputDir, path), '.json') )
		self._handle = None # Associated file handle, if one is open
		self._IsChangedCallback = IsChangedCallback # Callback to tell if the associated FileData object is changed.
		self._DataCallback = DataCallback # Callback to retrieve data from the associated FileData object.
		self._ReserveCallback = ReserveCallback # Callback to reserve file handle slot in FileManager
		self._TimerCallback = TimerCallback # Callback to progress the timer of the file FileManager update thread.
	def close(self):
		"Close the handle and set it to none."
		self.lock.acquire()
		if self._handle is not None:
			self._handle.close()
			self._handle = None
		self.lock.release()
	def check(self):
		"Determine if the file has been changed."
		self.lock.acquire()
		result = self._IsChangedCallback()
		self.lock.release()
		return result
	def update(self):
		"Update changes to the file."
		self.lock.acquire()
		if self._IsChangedCallback():
			wx.LogVerbose( ''.join( ("Flushing found changes to file at: '", self.path.replace('%', '%%'), "'") ) )
			if self._handle is None:
				self._ReserveCallback(self)
				try:
					self._handle = open(self.path, 'wb')
				except OSError as err:
					raise FileOpError(''.join( ('Failed to open file at "', self.path, '"') ), err.errno, err.strerror)
			self._handle.seek(0)
			self._handle.truncate()
			self._handle.write( self._DataCallback().encode('utf-8') )
			self._handle.flush()
			wx.LogVerbose( ''.join( ("Finished flushing changes to file at: '", self.path.replace('%', '%%'), "'") ) )
		self.lock.release()
	def PushUpdate(self):
		"Callback to use update as an alternative to it being called periodically by the file manager. If push updates are not enabled, then do nothing."
		if self._TimerCallback is not None:
			wx.LogVerbose( ''.join( ("Push updating file at path: '", self.path.replace('%', '%%'), "'") ) )
			self._TimerCallback()

# FileData object and exception definition
class unfound: # A type to differentiate from null (translated to None) when searching inside a JSON-derived object.
	pass

class ControlFileError(Exception):
	pass

class FileData:
	def SetTaglessTags( self, exclusions = () ):
		"Check if there are tags with 2 or more occurrences, if not, set the tagless tags, otherwise, clear them."
		if self.tags.ReturnHighestOccurrences() >= 2:
			self.tags.ClearContainer(self.TaglessTags)
		else:
			for t in self.TaglessTags.tags:
				if t.name not in exclusions:
					self.tags.SetObj(t)
	def SetName(self, name):
		"Set the name setting to the specified value. Set or unset the nameless tags, if it is or is not None, respectively."
		self.name = name
		if name is None:
			self.tags.SetContainer(self.NamelessTags)
		else:
			self.tags.ClearContainer(self.NamelessTags)
	def GetName(self):
		return self.name
	def SetSource(self, source):
		"Set the source setting to the specified value. Set or unset the sourceless tags, if it is or is not None, respectively."
		self.source = source
		if source is None:
			self.tags.SetContainer(self.SourcelessTags)
		else:
			self.tags.ClearContainer(self.SourcelessTags)
	def GetSource(self):
		return self.source
	def SetConditionalTags(self, name):
		"Set the conditional tags for a certain name."
		self.ConditionalTags.SetTags(name, self.tags)
	def SetConditionalInitTags(self, obj):
		"Set the conditional tags for names from the initial .JSON dictionary."
		self.ConditionalTags.SetTagsInit(obj, self.tags)
	def ClearConditionalTags(self, name):
		"Clear the conditional tags for a certain name."
		self.ConditionalTags.ClearTags(name, self.tags)
	def _BuildData(self):
		"Return the data fields formatted as a JSON string, and set the change status to false.."
		output = {'rating' : SAFETY_VALUES_LOOKUP[self.rating]}
		obj = {self.path : output}
		if self.name is not None:
			output['name'] = self.name
		if self.source is not None:
			output['source'] = self.source
		tags = self.tags.ReturnOccurrenceStrings()
		if tags:
			output['tags'] = tags
		return json.dumps( obj, separators=(',',':') )
	def _GetJSONTypeName(self, item):
		"Return a string containing the equivalent JSON type of the variable."
		if isinstance(item, dict):
			return 'object'
		elif isinstance(item, list) or isinstance(item, tuple):
			return 'array'
		elif isinstance(item, str):
			return 'string'
		elif isinstance(item, int) or isinstance(item, float):
			return 'number'
		elif item is True:
			return 'true'
		elif item is False:
			return 'false'
		elif isinstance(item, unfound):
			return 'unfound'
		else: # item is None:
			return 'null'
	def __init__(self, path, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags):
		# The data fields
		self.path = os.path.basename(path)
		self.rating = DefaultSafety
		self.tags = TagsContainer()

		self.name = None
		self.NamelessTags = NamelessTags
		self.SetName(DefaultName)

		self.source = None
		self.SourcelessTags = SourcelessTags
		self.SetSource(DefaultSource)

		self.ConditionalTags = ConditionalTags
		self.TaglessTags = TaglessTags
		self.SetTaglessTags()

		self._IsChanged = True
		self._DataState = self._BuildData() # The current output of the DataCallback, used to determine if _IsChanged should be set.
		self._lock = None # A lock within the ManagedFile object, used to synchronize updates.
		self._PushUpdate = None # A callback to push data to the associated ManagedFile object
	def lock(self):
		"Acquire self._lock if it is not None."
		if self._lock is not None:
			self._lock.acquire()
			return
	def unlock(self):
		"Release self._lock if it is not None."
		if self._lock is not None:
			self._lock.release()
	def PrepareChange(self):
		self.lock()
	def FinishChange(self):
		"Release self._lock if it is not None and set IsChanged to True."
		DataState = self._BuildData()
		if self._DataState != DataState:
			self._IsChanged = True
			self._DataState = DataState
		self._PushUpdate()
		self.unlock()
	def _LoadJSONName(self, obj):
		"Load the name field from the JSON object."
		name = obj.get( 'name', unfound() )
		if isinstance(name, str):
			self.name = name
		elif isinstance(name, unfound) or name is None:
			pass
		else:
			raise ControlFileError( ''.join( ("'name' field is '", self._GetJSONTypeName(name), "' but must be a string or null, or not included.") ) )
	def _LoadJSONSource(self, obj):
		"Load the source field from the JSON object."
		source = obj.get( 'source', unfound() )
		if isinstance(source, str):
			self.SetSource(source)
		elif isinstance(source, unfound) or source is None:
			pass
		else:
			raise ControlFileError( ''.join( ("'source' field is '", self._GetJSONTypeName(source), "' but must be a string or null, or not included.") ) )
	def _LoadJSONRating(self, obj):
		"Load the rating field from a JSON object."
		rating = obj.get( 'rating', unfound() )
		if isinstance(rating, str):
			found = SAFETY_NAMES_LOOKUP.get(rating, None)
			if found is None:
				raise ControlFileError( ''.join( ("Invalid safety name '", rating, "'. Valid choices are: 's', 'q', 'e', 'safe', 'questionable', 'explicit', 'Safe', 'Questionable', 'Explicit'") ) )
			self.rating = found
		else:
			raise ControlFileError( ''.join( ("'rating' field is '", self._GetJSONTypeName(rating), "' but must be included as a string. Valid choices are: 's', 'q', 'e', 'safe', 'questionable', 'explicit', 'Safe', 'Questionable', 'Explicit'") ) )
	def _LoadJSONTags(self, obj):
		"Load the tags field from the JSON object."
		tags = obj.get( 'tags', unfound() )
		if isinstance(tags, list):
			if len(tags) > 2:
				raise ControlFileError( ''.join ( ("'tags' field is an array, of ", str( len(tags) ), ' string elements in length, but must be 0 to 2.') ) )
			self.tags = TagsContainer()
			for l, s in enumerate(tags, start=1):
				if not isinstance(s, str):
					raise ControlFileError( ''.join( ("'tags' index ", str(l), " is '", self._GetJSONTypeName(s), "' but must be a string.") ) )
				NewTags = TagsContainer()
				NewTags.SetString(s, l)
				self.tags.SetContainer(NewTags)
				self.SetConditionalInitTags( NewTags.ReturnDict() )
		elif isinstance(tags, unfound):
			pass
		else:
			raise ControlFileError( ''.join ( ("'tags' field is '", self._GetJSONTypeName(tags), "' but must be an array, or not included. If an array, it must be 0 to 2 string elements in length.") ) )
	def LoadJSON(self, obj):
		"Load the settings field from a JSON object."
		self._LoadJSONName(obj)
		self._LoadJSONSource(obj)
		self._LoadJSONRating(obj)
		self._LoadJSONTags(obj)
		self._DataState = self._BuildData() # The current output of the DataCallback, used to determine if _IsChanged should be set.
		self._IsChanged = True
	def IsChangedCallback(self):
		"Return whether or not any of the data has been changed."
		return self._IsChanged
	def DataCallback(self):
		self._IsChanged = False
		return self._DataState
	def GetManagedFile(self, OutputDir, ReserveCallback, TimerCallback):
		"Create and return associated ManagedFile object."
		manager = ManagedFile(OutputDir, self.path, self.IsChangedCallback, self.DataCallback, ReserveCallback, TimerCallback)
		self._PushUpdate = manager.PushUpdate
		self._lock = manager.lock
		return manager

# The file manager and its exception and defaults
DEFAULT_MAX_OPEN_FILES = 20
DEFAULT_UPDATE_INTERVAL = 30.0

class FileManagerError(Exception):
	pass

class FileManager:
	def CheckAny(self):
		"Return if True on the first file in need of updating. Otherwise, return False."
		result = False
		for f in self._files:
			result = f.check()
			if result:
				break
		return result
	def UpdateAll(self):
		wx.LogMessage('Flushing changes to hard disk.')
		if not self.CheckAny():
			wx.LogMessage('No changes found.')
			return
		for f in self._files:
			f.update()
		wx.LogMessage('Completed hard disk flush.')
	def _OnStartUpdateTimer(self, message, arg2=None):
		if self._UpdateInterval == -1.0:
			return
		if self._UpdateInterval == 0.0:
			pub.sendMessage("FileUpdateClear", message=None)
		self._UpdateTimer = threading.Thread(name='Update Timer', target=self._UpdateThread, daemon=True)
		self._UpdateTimerRunning.set()
		self._UpdateTimer.start()
		wx.LogMessage('Update thread started.')
	def _OnFileUpdateForce(self, message, arg2=None):
		wx.LogMessage('Hard disk flush forced.')
		if self._UpdateInterval == -1.0:
			self.UpdateAll()
		else:
			self._UpdateTimerDelay.set()
	def OnExit(self, e):
		self.destroy()
		e.Skip()
	def __init__(self, MaxOpenFiles, UpdateInterval):
		if MaxOpenFiles < 0:
			raise FileManagerError( ''.join( ('MAX_OPEN_FILES of "', str(MaxOpenFiles), '" specified. This value must be greater than or equal to 0.') ) )
		self._MaxOpenFiles = MaxOpenFiles
		if UpdateInterval != -1.0 and UpdateInterval < 0:
			raise FileManagerError( ''.join( ('UPDATE_INTERVAL of "', str(UpdateInterval), '" specified. This value must be greater than or equal to 0 or equal -1.') ) )
		self._UpdateInterval = UpdateInterval

		self._UpdateTimer = None # Starts the _UpdateThread process
		self._UpdateTimerRunning = threading.Event() # Unset to disable the timer
		self._UpdateTimerDelay = threading.Event() # Waited on to delay the update loop. Can be set to awaken early.

		self.FilesLock = threading.Semaphore(1) # Mutex on _files and _OpenFiles
		self._files = [] # List of ManagedFile objects
		self._OpenFiles = [] # List of ManagedFile objects which have open handles

		self.ControlFiles = [] # List of FileData objects
		self.InputPaths = [] # List of paths for the respective FileData objects with prepended input directories

		pub.subscribe(self._OnStartUpdateTimer, "StartUpdateTimer")
		pub.subscribe(self._OnFileUpdateForce, "FileUpdateForce")
	def _UpdateThread(self):
		"The worker thread to loop through files and flush any changes to the disk."
		sw = wx.StopWatch()
		swStart = sw.Start
		swPause = sw.Pause
		swTimeInMicro = sw.TimeInMicro
		running = self._UpdateTimerRunning.is_set
		wait = self._UpdateTimerDelay.wait
		clear = self._UpdateTimerDelay.clear
		interrupted = self._UpdateTimerDelay.is_set
		UpdateInterval = self._UpdateInterval * 1000000.0
		CheckAny = self.CheckAny
		sendMessage = pub.sendMessage
		acquire = self.FilesLock.acquire
		UpdateAll = self.UpdateAll
		release = self.FilesLock.release
		UpdateState = False
		while running():
			CurrentTime = 0.0
			delta = 1000000.0
			while True:
				if UpdateInterval == 0:
					wait(None)
					break
				swStart()
				delta = float(delta) - 1000000.0
				interval = UpdateInterval - CurrentTime
				sendMessage("FileUpdateTick", message=interval)
				if interval >= 1000000.0:
					WaitTime = 1000000.0 - delta
					wait(WaitTime / 1000000.0)
					if interrupted():
						swPause()
						break
					CurrentTime += WaitTime
					NewUpdateState = CheckAny()
					if NewUpdateState != UpdateState:
						UpdateState = NewUpdateState
						if UpdateState:
							sendMessage("FileUpdatePending", message=None)
						else:
							sendMessage("FileUpdateClear", message=None)
				elif interval > 0:
					wait( (interval - delta) / 1000000.0 )
					swPause()
					break
				else:
					swPause()
					break
				delta = swTimeInMicro()
			acquire()
			UpdateAll()
			release()
			clear()
			sendMessage("FileUpdateClear", message=None)
			UpdateState = False
	def _StopUpdateTimer(self):
		if self._UpdateInterval == -1.0:
			self.UpdateAll()
			return
		self._UpdateTimerRunning.clear()
		self._UpdateTimerDelay.set()
		self._UpdateTimer.join()
		wx.LogMessage('Update thread stopped.')
	def ReserveOpenFileSlot(self, item):
		"Reserve a slot for a file to be held open. The max number is controlled by MAX_OPEN_FILES If there are no open slots, then"
		if item in self._OpenFiles:
			return
		if self._MaxOpenFiles != 0 and len(self._OpenFiles) == self._MaxOpenFiles:
			self._OpenFiles[0].close()
			wx.LogVerbose( ''.join( ("Removing file at path '",
									 self._OpenFiles[0].path.replace("%", "%%"),
									 "' from output cache index ",
									 str( len(self._OpenFiles) )
									)
								  )
						 )
			self._OpenFiles.pop(0)
		self._OpenFiles.append(item)
		wx.LogVerbose( ''.join( ("Added file at path '",
								 item.path.replace('%', '%%'),
								 "' to output cache index ",
								 str( len(self._OpenFiles) )
								)
							  )
					 )
	def AddFile(self, OutputDir, path, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags):
		"Add a FileData object and its associated MangedFile object, with all the proper callbacks set."
		wx.LogVerbose( ''.join( ("Registering file at path '", path.replace('%', '%%'), "'") ) )
		if path not in self.InputPaths:
			PushUpdate = None
			if self._UpdateInterval == 0.0:
				PushUpdate = self._UpdateTimerDelay.set
			self.ControlFiles.append( FileData(path, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags) )
			self.InputPaths.append(path)
			self._files.append( self.ControlFiles[-1].GetManagedFile(OutputDir, self.ReserveOpenFileSlot, PushUpdate) )
	def AddJSON(self, InputDir, OutputDir, obj, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags):
		"Loop through a .json object and load the settings to the FileData object associated with the respective path. If it does not exist, then create it first."
		for k, v in obj.items():
			self.AddFile(OutputDir, os.path.join(InputDir, k), DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags)
			ControlFile = self.ControlFiles[self.InputPaths.index( os.path.join(InputDir, k) )]
			ControlFile.PrepareChange()
			ControlFile.LoadJSON(v)
			ControlFile.FinishChange()
	def destroy(self):
		"Stop the update timers and destroy all handles."
		self._StopUpdateTimer()
		self.FilesLock.acquire()
		for f in self._files:
			f.close()
		self.FilesLock.release()
