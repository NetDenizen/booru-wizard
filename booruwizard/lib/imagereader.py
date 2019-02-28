import os

import wx

class ImageReaderError(Exception):
	def __init__(self, message, errno, strerror):
		super().__init__( ''.join( (message, ' [errno ', errno, ']: ', strerror) ) )

class ManagedImage:
	def __init__(self, path):
		self.path = path # Path to image
		self.image = None # WX image object
		self.DataSize = 0
		self.FileSize = 0
	def open(self):
		"Open the image path and set the WX image object."
		try:
			stream = open(self.path, mode='rb')
			self.image = wx.Image(stream)
			self.FileSize = os.fstat( stream.fileno() ).st_size
			stream.close()
			self.DataSize = len( self.image.GetDataBuffer() )
			if not self.image.IsOk():
				raise Exception()
		except: # TODO: Should this be more specific?
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

class ImageReader:
	def __init__(self, MaxBufSize):
		self._MaxBufSize = MaxBufSize # Maximum size of WX image data
		self._CurrentBufSize = 0 # Current size of WX image data
		self.images = [] # Array of all ManagedImage's
		self._OpenImages = [] # Array of ManagedImage's for which a WX image object exists
	def _activate(self, image):
		"Add the image object's WX Image object to the open images array if it is not None."
		if image.image is None:
			return
		self._OpenImages.append(image)
		self._CurrentBufSize += image.DataSize
	def _add(self, path):
		"Add path to images array and open it if there is any space remaining."
		image = ManagedImage(path)
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
			self._OpenImages.pop(0)
	def get(self, idx):
		"Return WX image object for the image managed at the index."
		if self.images[idx].image is None:
			self.images[idx].open()
			self._CullSpace(self.images[idx].DataSize)
			self._activate(self.images[idx])
		return self.images[idx]
	def GetMaxBufSize(self):
		return self._MaxBufSize
	def GetCurrentBufSize(self):
		return self._CurrentBufSize
	def GetNumOpenImages(self):
		return len(self._OpenImages)
	def GetCacheIndex(self, image):
		return self._OpenImages.index(image)
