"Components associated with reading image files."

import os

import wx

class ImageReaderError(Exception):
	pass

class ImageOpenError(ImageReaderError):
	pass

class ImageConditionError(ImageReaderError):
	pass

class ManagedImage:
	def __init__(self, parent, idx, path):
		self.parent = parent
		self.idx = idx
		self.path = path # Path to image
		self.image = None # WX image object
		self.DataSize = 0
		self.FileSize = 0
		self.ImageConditionsHandled = False
	def open(self):
		"Open the image path and set the WX image object."
		if self.image is not None:
			return
		try:
			wx.LogMessage( ''.join( ("Loading image at path '", self.path.replace('%', '%%'), "'") ) )
			stream = open(self.path, mode='rb')
			self.image = wx.Image(stream)
			self.FileSize = os.fstat( stream.fileno() ).st_size
			stream.close()
			if not self.image.IsOk():
				raise ImageOpenError()
			self.DataSize = len( self.image.GetDataBuffer() )
			if not self.ImageConditionsHandled:
				f = self.parent.OutputFiles.ControlFiles[self.idx]
				for c in self.parent.ImageConditions:
					if self.CheckImageCondition(c.condition):
						f.PrepareChange()
						self.parent.TagsTracker.SubStringList(f.tags.ReturnStringList(), 1)
						f.tags.SetString(c.TagString, 1)
						f.SetConditionalTags(c.TagString)
						f.SetTaglessTags()
						self.parent.TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)
						f.FinishChange()
				self.ImageConditionsHandled = True
		except (OSError, ImageOpenError):
			self.image = None
			self.DataSize = 0
			self.FileSize = 0
	def close(self):
		"Destroy the WX image object and set it to None"
		if self.image is None:
			return
		self.image.Destroy()
		self.image = None
		self.DataSize = 0
		self.FileSize = 0
	def CheckImageCondition(self, s):
		if self.image is None:
			return False
		ErrorMessage = ''.join( ("Failed to parse condition string of '", s, "' for image at path'", self.path.replace('%', '%%'), "'.") )
		tokens = s.split()
		if len(tokens) != 3:
			raise ImageConditionError( ''.join( (ErrorMessage, '(', str( len(tokens) ), ' space-separated tokens.)') ) )
		CompareFrom = tokens[0].lower()
		if CompareFrom == 'width':
			CompareFrom = self.image.GetWidth()
		elif CompareFrom == 'height':
			CompareFrom = self.image.GetHeight()
		elif CompareFrom == 'pixels':
			CompareFrom = self.image.GetWidth() * self.image.GetHeight()
		elif CompareFrom == 'size':
			CompareFrom = self.FileSize
		else:
			raise ImageConditionError( ''.join( (ErrorMessage, "(First token must be 'width', 'height', 'pixels', or 'size'. We found '", CompareFrom, "'.)") ) )
		CompareTo = tokens[2]
		try:
			CompareTo = int(tokens[2])
		except (ValueError, TypeError):
			raise ImageConditionError( ''.join( (ErrorMessage, "(Third token must be an integer. We found '", CompareTo, "'.)") ) )
		result = None
		if tokens[1] == '<':
			result = CompareFrom < CompareTo
		elif tokens[1] == '<=':
			result = CompareFrom <= CompareTo
		elif tokens[1] == '==' or tokens[1] == '=':
			result = CompareFrom == CompareTo
		elif tokens[1] == '>=':
			result = CompareFrom >= CompareTo
		elif tokens[1] == '>':
			result = CompareFrom > CompareTo
		else:
			raise ImageConditionError( ''.join( (ErrorMessage, "(Second token must be '<', '<=', '==', '=', '>=', or '>'. We found '", tokens[1], "'.)") ) )
		return result

class ImageReader:
	def __init__(self, MaxBufSize, TagsTracker, OutputFiles, ImageConditions):
		self._MaxBufSize = MaxBufSize # Maximum size of WX image data
		self._CurrentBufSize = 0 # Current size of WX image data
		self.images = [] # Array of all ManagedImage's
		self._OpenImages = [] # Array of ManagedImage's for which a WX image object exists
		self.TagsTracker = TagsTracker
		self.OutputFiles = OutputFiles
		self.ImageConditions = ImageConditions
	def _activate(self, image):
		"Add the image object's WX Image object to the open images array if it is not None."
		if image.image is None:
			return
		wx.LogVerbose( ''.join( ('Adding image of ', str(image.DataSize), " bytes at path '", image.path.replace('%', '%%'),
								 "' to image data cache index ", str( len(self._OpenImages) )
								)
							  )
					 )
		self._OpenImages.append(image)
		self._CurrentBufSize += image.DataSize
	def _add(self, path):
		"Add path to images array and open it if there is any space remaining."
		image = ManagedImage(self, len(self.images), path)
		image.open()
		if image.DataSize != 0 and (self._CurrentBufSize + image.DataSize <= self._MaxBufSize or len(self._OpenImages) == 0):
			self._activate(image)
		else:
			image.close()
		self.images.append(image)
	def AddPathsList(self, paths):
		for p in paths:
			self._add(p)
	def _CullSpace(self, size):
		"Starting from the first index of the open images array, start closing images until their collective size is below the maximum buffer size."
		while len(self._OpenImages) > 0 and self._CurrentBufSize + size > self._MaxBufSize:
			self._CurrentBufSize -= self._OpenImages[0].DataSize
			self._OpenImages[0].close()
			wx.LogVerbose( ''.join( ('Removing image of ', str(self._OpenImages[0].DataSize), " bytes at path '",
									 self._OpenImages[0].path.replace('%', '%%'), "' from image data cache index ",
									 str( len(self._OpenImages) )
									)
								  )
						 )
			self._OpenImages.pop(0)
	def get(self, idx):
		"Return WX image object for the image managed at the index."
		return self.images[idx]
	def load(self, idx):
		"Return WX image object for the image managed at the index, after loading its associated image data."
		if self.images[idx].image is None:
			self.images[idx].open()
			self._CullSpace(self.images[idx].DataSize)
			self._activate(self.images[idx])
		return self.get(idx)
	def GetMaxBufSize(self):
		return self._MaxBufSize
	def GetCurrentBufSize(self):
		return self._CurrentBufSize
	def GetNumOpenImages(self):
		return len(self._OpenImages)
	def GetCacheIndex(self, image):
		return self._OpenImages.index(image)
	def FinishImageConditions(self):
		for i in self.images:
			if not i.ImageConditionsHandled:
				i.open()
				i.close()
