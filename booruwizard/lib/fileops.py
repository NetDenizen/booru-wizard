import threading
import os.path
from enum import Enum
import json

from booruwizard.lib.tag import TagsContainer

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
	def __init__(self, OutputDir, PushUpdatesEnabled, path, IsChangedCallback, DataCallback, ReserveCallback):
		self.lock = threading.Semaphore(1)
		self.PushUpdatesEnabled = PushUpdatesEnabled # Determines if the FileData object can push updates to this object.
		self._path = ''.join( ( os.path.join(OutputDir, path), '.json' ) )
		self._handle = None # Associated file handle, if one is open
		self._IsChangedCallback = IsChangedCallback # Callback to tell if the associated FileData object is changed.
		self._DataCallback = DataCallback # Callback to retrieve data from the associated FileData object.
		self._ReserveCallback = ReserveCallback # Callback to reserve file handle slot in FileManager
	def close(self):
		"Close the handle and set it to none."
		self.lock.acquire()
		if self._handle is not None:
			self._handle.close()
			self._handle = None
		self.lock.release()
	def update(self):
		"Update changes to the file."
		self.lock.acquire()
		if self._IsChangedCallback():
			if self._handle is None:
				self._ReserveCallback(self)
				try:
					self._handle = open(self._path, 'wb')
				except OSError as err:
					raise FileOpError( ''.join( ('Failed to open file at "', self._path, '"') ), err.errno, err.strerror )
			self._handle.seek(0)
			self._handle.truncate()
			self._handle.write( self._DataCallback().encode('utf-8') )
			self._handle.flush()
		self.lock.release()
	def PushUpdate(self):
		"Callback to use update as an alternative to it being called periodically by the file manager. If push updates are not enabled, then do nothing."
		if self.PushUpdatesEnabled:
			self.update()

# FileData object and exception definition
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
	def SetSource(self, source):
		"Set the source setting to the specified value. Set or unset the sourceless tags, if it is or is not None, respectively."
		self.source = source
		if source is None:
			self.tags.SetContainer(self.SourcelessTags)
		else:
			self.tags.ClearContainer(self.SourcelessTags)
	def SetConditionalTags(self, name):
		"Set the conditional tags for a certain name."
		self.ConditionalTags.SetTags(name, self.tags)
	def SetConditionalInitTags(self, obj):
		"Set the conditional tags for names from the initial .JSON dictionary."
		self.ConditionalTags.SetTagsInit(obj, self.tags)
	def ClearConditionalTags(self, name):
		"Clear the conditional tags for a certain name."
		self.ConditionalTags.ClearTags(name, self.tags)
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
		self._lock = None # A lock within the ManagedFile object, used to synchronize updates.
		self._PushUpdate = None # A callback to push data to the associated ManagedFile object
		#TODO: Other default tag stuff
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
		self.unlock()
		self._IsChanged = True
	def LoadJSON(self, obj):
		"Load the settings from a string containing JSON data to this object."
		name = obj.get('name', None)
		if name is not None:
			self.name = name
		source = obj.get('source', None)
		if source is not None:
			self.SetSource(source)
		tags = obj.get('tags', None)
		if tags is not None:
			self.tags = TagsContainer()
			self.tags.SetDict(tags)
			self.SetConditionalInitTags(tags)
		rating = obj.get('rating', None)
		if rating is not None:
			found = SAFETY_NAMES_LOOKUP.get(rating, None)
			if found is None:
				raise ControlFileError( ''.join( ("Invalid safety name '", rating, "'") ) )
			self.rating = found
	def IsChangedCallback(self):
		"Return whether or not any of the data has been changed. Once that has been checked, set the change status to false."
		IsChanged = self._IsChanged
		self._IsChanged = False
		return IsChanged
	def DataCallback(self):
		"Return the data fields formatted as a JSON string."
		obj = { self.path :
				{ 'name'   : self.name,
				  'source' : self.source,
				  'rating' : SAFETY_VALUES_LOOKUP[self.rating],
				  'tags'   : self.tags.ReturnDict()
				}
			  }
		return json.dumps(obj)
	def GetManagedFile(self, OutputDir, PushUpdatesEnabled, ReserveCallback):
		"Create and return associated ManagedFile object."
		manager = ManagedFile(OutputDir, PushUpdatesEnabled, self.path, self.IsChangedCallback, self.DataCallback, ReserveCallback)
		self._PushUpdate = manager.PushUpdate
		self._lock = manager.lock
		return manager

# The file manager and its exception and defaults
DEFAULT_MAX_OPEN_FILES = 20
DEFAULT_UPDATE_INTERVAL = 30.0
DEFAULT_MAX_IMAGE_BUFSIZE = 100000000

class FileManagerError(Exception):
	pass

#TODO: Use semaphore for MaxOpenFiles itself?
class FileManager:
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
		self.paths = [] # List of original paths for the respective FileData objects
		self.InputPaths = [] # List of paths for the respective FileData objects with prepended input directories
	def UpdateAll(self):
		for f in self._files:
			f.update()
	def _UpdateThread(self):
		"The worker thread to loop through files and flush any changes to the disk."
		while self._UpdateTimerRunning.is_set():
			self._UpdateTimerDelay.wait(self._UpdateInterval)
			self.FilesLock.acquire()
			self.UpdateAll()
			self.FilesLock.release()
	def StartUpdateTimer(self):
		if self._UpdateInterval == -1.0 or self._UpdateInterval == 0.0:
			return
		self._UpdateTimer = threading.Thread( name='Update Timer', target=self._UpdateThread, daemon=True )
		self._UpdateTimerRunning.set()
		self._UpdateTimer.start()
	def _StopUpdateTimer(self):
		if self._UpdateInterval == -1.0 or self._UpdateInterval == 0.0:
			return
		self._UpdateTimerRunning.clear()
		self._UpdateTimerDelay.set()
		self._UpdateTimer.join()
	def ReserveOpenFileSlot(self, item):
		"Reserve a slot for a file to be held open. The max number is controlled by MAX_OPEN_FILES If there are no open slots, then"
		if item in self._OpenFiles:
			return
		if self._MaxOpenFiles != 0 and len(self._OpenFiles) == self._MaxOpenFiles:
			self._OpenFiles[0].close()
			self._OpenFiles.pop(0)
		self._OpenFiles.append(item)
	def AddFile(self, InputDir, OutputDir, path, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags):
		"Add a FileData object and its associated MangedFile object, with all the proper callbacks set."
		if path in self.paths:
			ControlFile = self.ControlFiles[self.paths.index(path)]
			ControlFile.PrepareChange()
			#TODO: To function?
			ControlFile.name = DefaultName
			ControlFile.source = DefaultSource
			ControlFile.safety = DefaultSafety
			ControlFile.SourcelessTags = SourcelessTags
			ControlFile.FinishChange()
		else:
			PushUpdatesEnabled = False
			if self._UpdateInterval == 0.0:
				PushUpdatesEnabled = True
			self.ControlFiles.append( FileData(path, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags) )
			self.paths.append(path)
			self.InputPaths.append( os.path.join(InputDir, path) )
			self._files.append( self.ControlFiles[-1].GetManagedFile(OutputDir, PushUpdatesEnabled, self.ReserveOpenFileSlot) )
	def AddJSON(self, InputDir, OutputDir, obj, DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags):
		"Loop through a .json object and load the settings to the FileData object associated with the respective path. If it does not exist, then create it first."
		for k, v in obj.items():
			if os.path.join(InputDir, k) not in self.InputPaths:
				self.AddFile(InputDir, OutputDir, os.path.join(InputDir, k), DefaultName, DefaultSource, DefaultSafety, ConditionalTags, NamelessTags, SourcelessTags, TaglessTags)
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
