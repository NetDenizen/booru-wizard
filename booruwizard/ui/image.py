import wx
from pubsub import pub

from booruwizard.lib.tag import tag, TagsContainer
from booruwizard.lib.template import question, option, OptionQuestion, QuestionType, OptionQuestionType
from booruwizard.lib.imagereader import ManagedImage, ImageReader
from booruwizard.lib.fileops import safety, FileData, FileManager

#TODO: Should we have a control to affect the scaling (maybe an alternate scrollbar setting), or to change the background color?
class ImagePanel(wx.Panel):
	def _SetBitmap(self):
		"Load the image at pos in the bitmap at array and scale it to fit the panel."
		image = self.bitmaps.get(self.pos)
		if image is None:
			self.DisplayedBitmap.SetBitmap( wx.Bitmap( wx.Image(1, 1) ) )
			self.sizer.Layout()
			return
		ImageWidth = image.GetWidth()
		ImageHeight = image.GetHeight()
		PanelSize = self.GetSize()
		PanelWidth = PanelSize.GetWidth()
		PanelHeight = PanelSize.GetHeight()
		if ImageWidth > ImageHeight:
			NewWidth = PanelWidth
			NewHeight = PanelHeight * (ImageHeight / ImageWidth)
		else:
			NewWidth = PanelWidth * (ImageWidth / ImageHeight)
			NewHeight = PanelHeight
		image = image.Scale(NewWidth, NewHeight, wx.IMAGE_QUALITY_HIGH) # TODO: Should we use high quality rescaling?
		self.DisplayedBitmap.SetBitmap( wx.Bitmap(image) )
		self.sizer.Layout()
	def _OnSize(self, e):
		"Bound to EVT_SIZE; mainly to update the scaling of the image on resize of the panel."
		self._SetBitmap()
		e.Skip()
	def _OnIndex(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		if 0 <= message < len(self.bitmaps.images):
			self.pos = message
		self._SetBitmap()
	def _OnLeft(self, message, arg2=None):
		"Shift to the left (-1) image to the current position in the bitmap array if the position is greater than 0. Otherwise, loop around to the last item."
		if self.pos == 0:
			self.pos = len(self.bitmaps.images) - 1
		else:
			self.pos -= 1
		self._SetBitmap()
	def _OnRight(self, message, arg2=None):
		"Shift to the right (+1) image to the current position in the bitmap array if the position is less than the length of the bitmap array. Otherwise, loop around to the last item."
		if self.pos >= len(self.bitmaps.images) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._SetBitmap()
	def __init__(self, parent, MaxBufSize, paths):
		wx.Panel.__init__(self, parent=parent)
		self.SetOwnBackgroundColour( wx.Colour(0, 0, 0) ) # Black # TODO: Can we use 'color'? Should we use the color database?

		self.pos = 0 # Position in bitmaps
		self.bitmaps = ImageReader(MaxBufSize)
		self.DisplayedBitmap = wx.StaticBitmap(self) # Current image loaded and displayed
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.DisplayedBitmap, 1, wx.ALIGN_CENTER | wx.SHAPED)
		self.SetSizer(self.sizer)

		self.bitmaps.AddPathsList(paths)
		self._SetBitmap()

		self.Bind(wx.EVT_SIZE, self._OnSize)
		pub.subscribe(self._OnIndex, "IndexImage")
		pub.subscribe(self._OnLeft, "LeftImage")
		pub.subscribe(self._OnRight, "RightImage")

class ImageLabel(wx.Panel):
	def _SetLabels(self):
		"Set the path label to show the path at pos in the paths array, and the index label to show pos + 1 out of length of paths array."
		self.PathLabel.SetValue(self.paths[self.pos])
		self.IndexEntry.SetValue( str(self.pos + 1) )
		self.IndexLabel.SetLabel( ''.join( ( ' /', str( len(self.paths) ) ) ) )
	def _OnIndexEntry(self, e):
		"Send a LEVT_INDEX_IMAGE event, if the index value can be converted to an Int; otherwise, reset labels."
		try:
			pub.sendMessage("IndexImage", message=int( self.IndexEntry.GetValue() ) - 1)
		except ValueError: # TODO: Should this work with any exception?
			self._SetLabels()
		e.Skip()
	def _OnIndex(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		if 0 <= message < len(self.paths):
			self.pos = message
		self._SetLabels()
	def _OnLeft(self, message, arg2=None):
		"Shift to the left (-1) path to the current position in the paths array if the position is greater than 0. Otherwise, loop around to the last item."
		if self.pos == 0:
			self.pos = len(self.paths) - 1
		else:
			self.pos -= 1
		self._SetLabels()
	def _OnRight(self, message, arg2=None):
		"Shift to the right (+1) path to the current position in the paths array if the position is less than the length of the paths array. Otherwise, loop around to the first item."
		if self.pos >= len(self.paths) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._SetLabels()
	def __init__(self, parent, paths):
		wx.Panel.__init__(self, parent=parent)

		self.pos = 0 # Position in paths
		self.paths = paths
		self.PathLabel = wx.TextCtrl(self, style= wx.TE_READONLY | wx.TE_NOHIDESEL) # Path of current image
		self.IndexEntry = wx.TextCtrl(self, style= wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Editable display for current image index
		self.IndexLabel = wx.StaticText(self, style= wx.ALIGN_CENTER) # Static part of image index display
		self.PathLabelTip = wx.ToolTip('Image path')
		self.IndexEntryTip = wx.ToolTip('Image index entry')
		self.IndexLabelTip = wx.ToolTip('Total number of images')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.PathLabel.SetToolTip(self.PathLabelTip)
		self.IndexEntry.SetToolTip(self.IndexEntryTip)
		self.IndexLabel.SetToolTip(self.IndexLabelTip)

		self.sizer.Add(self.PathLabel, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self.PathLabel.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		self._SetLabels()

		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		pub.subscribe(self._OnIndex, "IndexImage")
		pub.subscribe(self._OnLeft, "LeftImage")
		pub.subscribe(self._OnRight, "RightImage")

class ImageContainer(wx.Panel):
	def __init__(self, parent, MaxBufSize, paths):
		wx.Panel.__init__(self, parent=parent)

		self.image = ImagePanel(self, MaxBufSize, paths)
		self.label = ImageLabel(self, paths)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.image, 1, wx.ALIGN_CENTER | wx.SHAPED)
		self.sizer.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)
