import wx
from pubsub import pub

from booruwizard.lib.imagereader import ImageReader

#TODO: Should we have a control to affect the scaling (maybe an alternate scrollbar setting), or to change the background color?
class ImageDisplay(wx.Panel):
	def _OnPaint(self, e):
		"Load the image at pos in the bitmap at array and scale it to fit the panel. If the image has alpha, overlay it with an image from the background manager."
		dc = wx.PaintDC(self)
		if self.bitmap is None:
			return
		ImageWidth = self.bitmap.GetWidth()
		ImageHeight = self.bitmap.GetHeight()
		PanelSize = self.GetSize()
		PanelWidth = PanelSize.GetWidth()
		PanelHeight = PanelSize.GetHeight()
		if ImageWidth > ImageHeight:
			NewWidth = PanelWidth
			NewHeight = PanelHeight * (ImageHeight / ImageWidth)
		else:
			NewWidth = PanelWidth * (ImageWidth / ImageHeight)
			NewHeight = PanelHeight
		DiffWidth = (PanelWidth - NewWidth) / 2
		if DiffWidth < 0:
			DiffWidth = 0
		DiffHeight = (PanelHeight - NewHeight) / 2
		if DiffHeight < 0:
			DiffHeight = 0
		image = self.bitmap.Scale(NewWidth, NewHeight, wx.IMAGE_QUALITY_HIGH) # TODO: Should we use high quality rescaling?
		dc.DrawBitmap( wx.Bitmap.FromBuffer( NewWidth, NewHeight, self.BackgroundManager.get(NewWidth, NewHeight) ), DiffWidth, DiffHeight, True )
		dc.DrawBitmap( wx.Bitmap(image), DiffWidth, DiffHeight, True )
	def __init__(self, parent, BackgroundManager):
		wx.Panel.__init__(self, parent=parent)
		self.bitmap = None
		self.BackgroundManager = BackgroundManager

		self.Bind(wx.EVT_PAINT, self._OnPaint)

class ImagePanel(wx.Panel):
	def _HumanSize(self, val):
		"Return a string containing the human readable representation of size 'val'."
		if val // 1024 == 0:
			return ''.join( ( str(val), 'bytes' ) )
		elif val // 1048576 == 0:
			return ''.join( ( str( round(val / 1000.0, 3) ), ' kB' ) )
		else:
			return ''.join( ( str( round(val / 1000000.0, 6) ), ' MB' ) )
	def _MaxExtent(self, items, strings):
		MaxWidth = 0
		MaxExtent = None
		for i, s in zip(items, strings):
			extent = i.GetTextExtent(s)
			if extent.GetWidth() > MaxWidth:
				MaxExtent = extent
		return MaxExtent
	def _update(self):
		"Update the current bitmap, and the information display."
		image = self.bitmaps.get(self.pos)
		self.image.bitmap = image.image
		if self.image.bitmap is not None:
			size = self.image.bitmap.GetSize()
			ResolutionString = ''.join( ( 'Resolution: ', str( size.GetWidth() ), 'x', str( size.GetHeight() ), ' (', str( size.GetWidth() * size.GetHeight() ), ' pixels)' ) )
			FileSizeString = ''.join( ( 'File size: ', self._HumanSize( image.FileSize ) ) )
			DataSizeString = ''.join( ( 'Data size: ', self._HumanSize( image.DataSize ), ' / ', self._HumanSize( self.bitmaps.GetCurrentBufSize() ), ' / ', self._HumanSize( self.bitmaps.GetMaxBufSize() ), ' (', str( self.bitmaps.GetNumOpenImages() ), ')' ) )
			MaxExtent = self._MaxExtent(
										 (self.ResolutionDisplay, self.FileSizeDisplay, self.DataSizeDisplay),
										 (ResolutionString, FileSizeString, DataSizeString)
									   )
			self.ResolutionDisplay.SetLabel(ResolutionString)
			self.FileSizeDisplay.SetLabel(FileSizeString)
			self.DataSizeDisplay.SetLabel(DataSizeString)
			self.RightPanelDummy.SetMinSize(MaxExtent)
		else:
			self.ResolutionDisplay.SetLabel('File failed to load')
			self.RightPanelDummy.SetMinSize( self.ResolutionDisplay.GetTextExtent('File failed to load') )
		self.Update()
		self.Layout()
		self.Refresh()
	def _OnIndex(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		if 0 <= message < len(self.bitmaps.images):
			self.pos = message
		self._update()
	def _OnLeft(self, message, arg2=None):
		"Shift to the left (-1) image to the current position in the bitmap array if the position is greater than 0. Otherwise, loop around to the last item."
		if self.pos == 0:
			self.pos = len(self.bitmaps.images) - 1
		else:
			self.pos -= 1
		self._update()
	def _OnRight(self, message, arg2=None):
		"Shift to the right (+1) image to the current position in the bitmap array if the position is less than the length of the bitmap array. Otherwise, loop around to the last item."
		if self.pos >= len(self.bitmaps.images) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._update()
	def __init__(self, parent, MaxBufSize, paths, BackgroundManager):
		wx.Panel.__init__(self, parent=parent)

		self.pos = 0 # Position in bitmaps
		self.bitmaps = ImageReader(MaxBufSize)
		self.ResolutionDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays the resolution of the current image
		self.FileSizeDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays the size of the current image
		self.DataSizeDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays the size of the current image
		self.DataSizeTip = wx.ToolTip('Current/Cumulative/Maximum (Number of files loaded)')
		self.image = ImageDisplay(self, BackgroundManager)
		self.RightPanelDummy = wx.Window(self)
		self.LeftPaneSizer = wx.BoxSizer(wx.VERTICAL)
		self.RightPaneSizer = wx.BoxSizer(wx.VERTICAL)
		self.MainSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.LeftPaneSizer.Add(self.ResolutionDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.Add(self.FileSizeDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.Add(self.DataSizeDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)

		self.RightPaneSizer.Add(self.RightPanelDummy, 0, wx.ALIGN_TOP | wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT)

		self.MainSizer.Add(self.LeftPaneSizer, 0, wx.ALIGN_LEFT | wx.LEFT | wx.EXPAND)
		self.MainSizer.Add(self.image, 1, wx.ALIGN_CENTER | wx.CENTER | wx.SHAPED)
		self.MainSizer.Add(self.RightPaneSizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.EXPAND)
		self.SetSizer(self.MainSizer)

		self.DataSizeDisplay.SetToolTip(self.DataSizeTip)
		self.bitmaps.AddPathsList(paths)
		self._update()

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
		"Send an IndexImage message, if the index value can be converted to an Int; otherwise, reset labels."
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
	def _OnFocusImageIndex(self, message, arg2=None):
		self.IndexEntry.SetFocus()
	def _OnFocusPathLabel(self, message, arg2=None):
		self.PathLabel.SetFocus()
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

		self.sizer.Add(self.PathLabel, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self.PathLabel.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		self._SetLabels()

		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		pub.subscribe(self._OnIndex, "IndexImage")
		pub.subscribe(self._OnLeft, "LeftImage")
		pub.subscribe(self._OnRight, "RightImage")
		pub.subscribe(self._OnFocusImageIndex, "FocusImageIndex")
		pub.subscribe(self._OnFocusPathLabel, "FocusPathLabel")

class ImageContainer(wx.Panel):
	def __init__(self, parent, MaxBufSize, paths, BackgroundManager):
		wx.Panel.__init__(self, parent=parent)

		self.image = ImagePanel(self, MaxBufSize, paths, BackgroundManager)
		self.label = ImageLabel(self, paths)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.image, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)
