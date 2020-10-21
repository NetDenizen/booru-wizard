"The components associated with the image (topmost) GUI frame."

from math import floor

import wx
from pubsub import pub

from booruwizard.lib.imagereader import ImageReader
from booruwizard.lib.viewport import ViewPortState
from booruwizard.ui.common import PathEntry, CircularCounter, RenderThreeIfMid, TagSearch

#TODO: Should we have a control to affect the scaling (maybe an alternate scrollbar setting), or to change the background color?
class ImageDisplay(wx.Panel):
	def _UpdateMove(self):
		self.viewport.UpdateBackground(self.viewport.DisplayWidth, self.viewport.DisplayHeight)
		self.viewport.UpdateImage(self.image, self.quality)
	def _OnPanLeft(self, message, arg2=None):
		self.viewport.ApplyMove(self.viewport.PanInterval * -1.0, 0.0)
		self._UpdateMove()
	def _OnPanRight(self, message, arg2=None):
		self.viewport.ApplyMove(self.viewport.PanInterval, 0.0)
		self._UpdateMove()
	def _OnPanUp(self, message, arg2=None):
		self.viewport.ApplyMove(0.0, self.viewport.PanInterval * -1.0)
		self._UpdateMove()
	def _OnPanDown(self, message, arg2=None):
		self.viewport.ApplyMove(0.0, self.viewport.PanInterval)
		self._UpdateMove()
	def _OnZoomIn(self, message, arg2=None):
		self.viewport.ApplyZoomTimes(True, 1)
		self._UpdateMove()
	def _OnZoomOut(self, message, arg2=None):
		self.viewport.ApplyZoomTimes(False, 1)
		self._UpdateMove()
	def _OnZoomFit(self, message, arg2=None):
		self.viewport.ApplyFit()
		self._UpdateMove()
	def _OnZoomActualSize(self, message, arg2=None):
		self.viewport.ApplyActualSize()
		self._UpdateMove()
	def _OnMouseDown(self, e):
		if self.image is None:
			return
		self.MouseStartX = e.GetX()
		self.MouseStartY = e.GetY()
		self.MouseDown = True
		if self.viewport.ZoomLevel != self.viewport.FitLevel:
			self.SetCursor( wx.Cursor(wx.CURSOR_CROSS) )
		e.Skip()
	def _OnMouseUp(self, e):
		if self.image is None:
			return
		self.MouseStartX = e.GetX()
		self.MouseStartY = e.GetY()
		self.MouseDown = False
		self.SetCursor( wx.Cursor(wx.CURSOR_ARROW) )
		e.Skip()
	def _OnMouseMotion(self, e):
		if not self.MouseDown:
			return
		XDiff = ( self.MouseStartX - e.GetX() ) / self.width
		YDiff = ( self.MouseStartY - e.GetY() ) / self.height
		self.MouseStartX = e.GetX()
		self.MouseStartY = e.GetY()
		self.viewport.ApplyMove(XDiff, YDiff)
		self._UpdateMove()
		e.Skip()
	def _OnSize(self, e):
		OldSteps = self.viewport.TotalSteps
		PanelSize = self.GetSize()
		PanelWidth = PanelSize.GetWidth()
		PanelHeight = PanelSize.GetHeight()
		if self.width != PanelWidth:
			self.ClearOnPaint = True
			self.width = PanelWidth
		else:
			self.ClearOnPaint = False
		if self.height != PanelHeight:
			self.ClearOnPaint = True
			self.height = PanelHeight
		else:
			self.ClearOnPaint = False
		self.viewport.UpdateBackground(self.width, self.height)
		self.viewport.ApplyZoomSteps(OldSteps)
		self.parent.UpdateZoomControls()
		self.viewport.UpdateImage(self.image, self.quality)
		e.Skip()
	def _OnPaint(self, e):
		"Load the image at pos in the bitmap at array and scale it to fit the panel. If the image has alpha, overlay it with an image from the background manager."
		dc = wx.AutoBufferedPaintDC(self)
		if self.ClearOnPaint:
			dc.Clear()
		if self.viewport.ImageBitmap is None:
			return
		if self.quality != self.CurrentQuality:
			self.CurrentQuality = self.quality
			self.viewport.UpdateImage(self.image, self.quality)
		dc.DrawBitmap(self.viewport.BackgroundBitmap, 0, 0, True)
		dc.DrawBitmap(self.viewport.ImageBitmap, 0, 0, True)
		self.Update()
		self.Refresh()
		e.Skip()
	def SetImage(self, image):
		self.image = image
		self.ClearOnPaint = False
		self.viewport.UpdateImage(self.image, self.quality)
	def __init__(self, parent, quality, viewport, keybinds):
		wx.Panel.__init__(self, parent=parent)
		self.parent = parent
		self.image = None
		self.height = None
		self.width = None
		self.ClearOnPaint = False
		self.quality = quality
		self.CurrentQuality = quality
		self.viewport = viewport

		self.MouseDown = False
		self.MouseStartX = None
		self.MouseStartY = None

		self.tip = wx.ToolTip( ''.join( ( "The currently loaded image. Click and drag in this field to move the view if the whole image isn't displayed at once.", RenderThreeIfMid(' (Pan Left: ', keybinds.get('pan_left'), ')'), RenderThreeIfMid(' (Pan Right: ', keybinds.get('pan_right'), ')'), RenderThreeIfMid(' (Pan Up: ', keybinds.get('pan_up'), ')'), RenderThreeIfMid(' (Pan Down: ', keybinds.get('pan_down'), ')') ) ) )
		self.SetToolTip(self.tip)

		self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

		self.Bind( wx.EVT_LEFT_DOWN, self._OnMouseDown, id=self.GetId() )
		self.Bind( wx.EVT_LEFT_UP, self._OnMouseUp, id=self.GetId() )
		self.Bind( wx.EVT_MOTION, self._OnMouseMotion, id=self.GetId() )
		self.Bind(wx.EVT_SIZE, self._OnSize)
		self.Bind(wx.EVT_PAINT, self._OnPaint)

		pub.subscribe(self._OnPanLeft, "PanLeft")
		pub.subscribe(self._OnPanRight, "PanRight")
		pub.subscribe(self._OnPanUp, "PanUp")
		pub.subscribe(self._OnPanDown, "PanDown")
		pub.subscribe(self._OnZoomIn, "ZoomIn")
		pub.subscribe(self._OnZoomOut, "ZoomOut")
		pub.subscribe(self._OnZoomFit, "ZoomFit")
		pub.subscribe(self._OnZoomActualSize, "ZoomActualSize")

class ImagePanel(wx.Panel):
	def _HumanSize(self, val):
		"Return a string containing the human readable representation of size 'val'."
		if val // 1024 == 0:
			return ''.join( (str(val), 'bytes') )
		elif val // 1048576 == 0:
			return ''.join( (str( round(val / 1000.0, 3) ), ' kB') )
		else:
			return ''.join( (str( round(val / 1000000.0, 6) ), ' MB') )
	def _UpdateImage(self):
		"Update the image panel."
		OldSteps = self.image.viewport.TotalSteps
		self.image.SetImage(self.bitmaps.load( self.pos.get() ).image)
		if self.image.viewport.image is not None:
			self.image.viewport.ApplyZoomSteps(OldSteps)
	def _UpdateImageData(self):
		"Update statistics about the image."
		image = self.bitmaps.get( self.pos.get() )
		if self.image.image is not None:
			size = self.image.image.GetSize()
			ResolutionString = ''.join( (
										 'Resolution: ', str( size.GetWidth() ), 'x', str( size.GetHeight() ),
										 ' (', str( size.GetWidth() * size.GetHeight() ), ' pixels)'
										)
									  )
			FileSizeString = ''.join( ( 'File size: ', self._HumanSize(image.FileSize) ) )
			DataSizeString = ''.join(
									  (
									   'Data size: ', self._HumanSize(image.DataSize), ' / ',
									   self._HumanSize( self.bitmaps.GetCurrentBufSize() ), ' / ',
									   self._HumanSize( self.bitmaps.GetMaxBufSize() ),
									   ' (', str( self.bitmaps.GetCacheIndex(image) + 1 ), '/', str( self.bitmaps.GetNumOpenImages() ), ')'
									  )
									)
		else:
			ResolutionString = 'File failed to load'
			FileSizeString = ''
			DataSizeString = ''
		self.ResolutionDisplay.SetLabel(ResolutionString)
		self.FileSizeDisplay.SetLabel(FileSizeString)
		self.DataSizeDisplay.SetLabel(DataSizeString)
	def UpdateZoomControls(self):
		"Update the zoom controls."
		if self.image.viewport.image is None:
			self.ZoomDisplay.SetLabel('')
			self.ZoomInButton.Disable()
			self.ZoomOutButton.Disable()
			self.ZoomFitButton.Disable()
			self.ZoomActualButton.Disable()
		else:
			dimensions = self.image.viewport.GetActualSizeRatio()
			self.ZoomDisplay.SetLabel( ''.join( (
												  'Zoom Level: ', str( round(dimensions[0], 3) ), ' ',
												  '(', str( floor(dimensions[1]) ), 'x', str( floor(dimensions[2]) ), ')',
												)
											  )
									 )
			ImageSize = self.image.image.GetSize()
			if (self.image.viewport.state == ViewPortState.ACTUAL and\
			   self.image.viewport.ZoomLevel == 1.0):
				self.ZoomActualButton.Disable()
			else:
				self.ZoomActualButton.Enable()
			if self.image.viewport.ZoomLevel == self.image.viewport.FitLevel:
				self.ZoomFitButton.Disable()
				self.ZoomOutButton.Disable()
			else:
				self.ZoomFitButton.Enable()
				self.ZoomOutButton.Enable()
			self.ZoomInButton.Enable()
	def _update(self):
		"Update the current bitmap, the information display, and controls."
		self._UpdateImage()
		self._UpdateImageData()
		self.UpdateZoomControls()
		self.Layout()
	def _OnFileUpdatePending(self, message, arg2=None):
		wx.CallAfter(self.OutputUpdateButton.Enable)
	def _OnFileUpdateClear(self, message, arg2=None):
		wx.CallAfter(self.OutputUpdateButton.Disable)
	def _OnFileUpdateTick(self, message, arg2=None):
		MessageSeconds = message / 1000000.0
		minutes = str( int(MessageSeconds // 60.0) )
		FullSeconds = str( round(MessageSeconds % 60.0, 3) )
		SplitSeconds = FullSeconds.split('.', 2)
		output = ''.join( ( 'Until Next Flush: ',
							minutes.zfill(2), ':', SplitSeconds[0].zfill(2), '.', SplitSeconds[1].ljust(3, '0') ) )
		wx.CallAfter(self.OutputUpdateTimer.SetLabel, output)
	def _OnImageQualityHigh21(self, message, arg2=None):
		"Set image quality to high 2+1 (box average on downscale, bicubic on upscale), update the radio button, and repaint the image."
		self.ImageQualityControl.SetSelection(0)
		self.image.quality = wx.IMAGE_QUALITY_HIGH
	def _OnImageQualityHigh2(self, message, arg2=None):
		"Set image quality to high 2 (bicubic), update the radio button, and repaint the image."
		self.ImageQualityControl.SetSelection(1)
		self.image.quality = wx.IMAGE_QUALITY_BICUBIC
	def _OnImageQualityHigh1(self, message, arg2=None):
		"Set image quality to high 1 (box average), update the radio button, and repaint the image."
		self.ImageQualityControl.SetSelection(2)
		self.image.quality = wx.IMAGE_QUALITY_BOX_AVERAGE
	def _OnImageQualityMedium(self, message, arg2=None):
		"Set image quality to medium (bilinear), update the radio button, and repaint the image."
		self.ImageQualityControl.SetSelection(3)
		self.image.quality = wx.IMAGE_QUALITY_BILINEAR
	def _OnImageQualityLow(self, message, arg2=None):
		"Set image quality to low (nearest neighbor), update the radio button, and repaint the image."
		self.ImageQualityControl.SetSelection(4)
		self.image.quality = wx.IMAGE_QUALITY_NEAREST
	def _OnImageQualityLeft(self, message, arg2=None):
		"Cycle through 'L', 'M', 'H1', 'H2', and 'H2+1' image quality radio button settings."
		if self.image.quality == wx.IMAGE_QUALITY_HIGH:
			self._OnImageQualityLow(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BICUBIC:
			self._OnImageQualityHigh21(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BOX_AVERAGE:
			self._OnImageQualityHigh2(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BILINEAR:
			self._OnImageQualityHigh1(None)
		else: # self.image.quality == wx.IMAGE_QUALITY_NEAREST
			self._OnImageQualityMedium(None)
	def _OnImageQualityRight(self, message, arg2=None):
		"Cycle through 'H2+1', 'H2', 'H1', 'M', and 'L' image quality radio button settings."
		if self.image.quality == wx.IMAGE_QUALITY_HIGH:
			self._OnImageQualityHigh2(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BICUBIC:
			self._OnImageQualityHigh1(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BOX_AVERAGE:
			self._OnImageQualityMedium(None)
		elif self.image.quality == wx.IMAGE_QUALITY_BILINEAR:
			self._OnImageQualityLow(None)
		else: # self.image.quality == wx.IMAGE_QUALITY_NEAREST
			self._OnImageQualityHigh21(None)
	def _OnIndex(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		self.pos.set(message)
		self._update()
	def _OnLeft(self, message, arg2=None):
		"Shift to the left (-1) image to the current position in the bitmap array if the position is greater than 0. Otherwise, loop around to the last item."
		self.pos.dec()
		self._update()
	def _OnRight(self, message, arg2=None):
		"Shift to the right (+1) image to the current position in the bitmap array if the position is less than the length of the bitmap array. Otherwise, loop around to the last item."
		self.pos.inc()
		self._update()
	def _OnImageQualitySelect(self, e):
		"Bound to EVT_RADIOBOX; update image quality from the relevant radio box."
		selection = self.ImageQualityControl.GetSelection()
		if selection == 0 and self.image.quality != wx.IMAGE_QUALITY_HIGH:
			self.image.quality = wx.IMAGE_QUALITY_HIGH
		elif selection == 1 and self.image.quality != wx.IMAGE_QUALITY_BICUBIC:
			self.image.quality = wx.IMAGE_QUALITY_BICUBIC
		elif selection == 2 and self.image.quality != wx.IMAGE_QUALITY_BOX_AVERAGE:
			self.image.quality = wx.IMAGE_QUALITY_BOX_AVERAGE
		elif selection == 3 and self.image.quality != wx.IMAGE_QUALITY_BILINEAR:
			self.image.quality = wx.IMAGE_QUALITY_BILINEAR
		elif selection == 4 and self.image.quality != wx.IMAGE_QUALITY_NEAREST:
			self.image.quality = wx.IMAGE_QUALITY_NEAREST
		e.Skip()
	def _OnZoomIn(self, e):
		pub.sendMessage("ZoomIn", message=None)
		e.Skip()
	def _OnZoomOut(self, e):
		pub.sendMessage("ZoomOut", message=None)
		e.Skip()
	def _OnZoomFit(self, e):
		pub.sendMessage("ZoomFit", message=None)
		e.Skip()
	def _OnZoomActual(self, e):
		pub.sendMessage("ZoomActualSize", message=None)
		e.Skip()
	def _OnZoomInReceived(self, message, arg2=None):
		self.UpdateZoomControls()
		self.ZoomInButton.SetFocus()
	def _OnZoomOutReceived(self, message, arg2=None):
		self.UpdateZoomControls()
		if self.ZoomOutButton.IsEnabled():
			self.ZoomOutButton.SetFocus()
		else:
			self.ZoomInButton.SetFocus()
	def _OnZoomFitReceived(self, message, arg2=None):
		self.UpdateZoomControls()
		self.ZoomInButton.SetFocus()
	def _OnZoomActualReceived(self, message, arg2=None):
		self.UpdateZoomControls()
		if self.ZoomOutButton.IsEnabled():
			self.ZoomOutButton.SetFocus()
		else:
			self.ZoomInButton.SetFocus()
	def _OnOutputUpdateButton(self, e):
		pub.sendMessage("FileUpdateForce", message=None)
		e.Skip()
	def __init__(self, parent, OutputFiles, images, ImageQuality, ViewPort, keybinds):
		wx.Panel.__init__(self, parent=parent)

		self.pos = None # Position in bitmaps
		self.bitmaps = images
		self.ResolutionDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays the resolution of the current image
		self.FileSizeDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays the size of the current image
		self.DataSizeDisplay = wx.StaticText(self, style= wx.ALIGN_LEFT) # Displays statistics about imagebuffer usage
		self.ResolutionTip = wx.ToolTip('Resolution of current image: WidthxHeight (Number of Pixels)')
		self.FileSizeTip = wx.ToolTip('Size of current image file on disk. Not loaded into memory.')
		self.DataSizeTip = wx.ToolTip('Current/Cumulative/Maximum (Cache Index/Number of files loaded)')
		self.ImageQualityControl = wx.RadioBox(self, label='Image Quality:',
											   choices= ('H2+1', 'H2', 'H1', 'M', 'L'),
											   style= wx.RA_SPECIFY_COLS | wx.ALIGN_LEFT
											  )
		self.ImageQualityControlTip = wx.ToolTip( ''.join( ( 'Select the current quality of the image resizing algorithm.', RenderThreeIfMid(' (Cycle Left: ', keybinds.get('image_quality_left'), ')'), RenderThreeIfMid(' (Cycle Right: ', keybinds.get('image_quality_right'), ')') ) ) )
		self.OutputUpdateTimer = wx.StaticText(self, label='Automatic Flushing Disabled', style= wx.ALIGN_LEFT)
		self.OutputUpdateTimerTip = wx.ToolTip('Time until next automatic flush')
		self.OutputUpdateButton = wx.Button(self, label='Flush Changes', style=wx.BU_EXACTFIT)
		self.OutputUpdateButtonTip = wx.ToolTip( ''.join( ( 'Immediately flush output files to hard drive, if changed.', RenderThreeIfMid(' (', keybinds.get('flush_changes'), ')') ) ) )
		self.ZoomDisplay = wx.StaticText(self)
		self.ZoomDisplayTip = wx.ToolTip('Zoom ratio to actual size of image (Sample WidthxSample Height)')
		self.ZoomInButton = wx.Button(self, label="+", style=wx.BU_EXACTFIT)
		self.ZoomInButtonTip = wx.ToolTip( ''.join( ( 'Zoom in to displayed image.', RenderThreeIfMid(' (', keybinds.get('zoom_in'), ')') ) ) )
		self.ZoomOutButton = wx.Button(self, label="-", style=wx.BU_EXACTFIT)
		self.ZoomOutButtonTip = wx.ToolTip( ''.join( ( 'Zoom out from displayed image.', RenderThreeIfMid(' (', keybinds.get('zoom_out'), ')') ) ) )
		self.ZoomFitButton = wx.Button(self, label="FIT", style=wx.BU_EXACTFIT)
		self.ZoomFitButtonTip = wx.ToolTip( ''.join( ( 'Zoom to fit window.', RenderThreeIfMid(' (', keybinds.get('zoom_fit'), ')') ) ) )
		self.ZoomActualButton = wx.Button(self, label="1.0", style=wx.BU_EXACTFIT)
		self.ZoomActualButtonTip = wx.ToolTip( ''.join( ( 'Zoom to actual size (1.0 Zoom Ratio).', RenderThreeIfMid(' (', keybinds.get('zoom_actual_size'), ')') ) ) )
		self.ImageSearch = TagSearch(self, OutputFiles)
		self.ImageSearch.EntryTip = wx.ToolTip( ''.join( ( 'Tag search field. Enter space-separated tags to update menu. The image must contain all of these, or options may start with \'-\' to exclude them. Menu items will switch to the associated image.', RenderThreeIfMid(' (Focus: ', keybinds.get('select_tag_search'), ')'), RenderThreeIfMid(' (Open Menu: ', keybinds.get('select_tag_search_menu'), ')') ) ) )
		self.ImageSearch.LeftImageTip = wx.ToolTip( ''.join( ( 'Previous image in search results, relative to the currently loaded image.', RenderThreeIfMid(' (', keybinds.get('left_tag_search_result'), ')') ) ) )
		self.ImageSearch.RightImageTip = wx.ToolTip( ''.join( ( 'Next image in search results, relative to the currently loaded image.', RenderThreeIfMid(' (', keybinds.get('right_tag_search_result'), ')') ) ) )
		self.image = ImageDisplay(self, ImageQuality, ViewPort, keybinds)
		self.ImageSearchSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.ZoomControlSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.LeftPaneSizer = wx.BoxSizer(wx.VERTICAL)
		self.MainSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.ImageSearch.SelfBinds()
		self.ImageSearch.SelfPubSub()

		self.ImageSearchSizer.Add(self.ImageSearch.LeftImage, 0, wx.ALIGN_CENTER)
		self.ImageSearchSizer.AddStretchSpacer(1)
		self.ImageSearchSizer.Add(self.ImageSearch.RightImage, 0, wx.ALIGN_CENTER)
		self.ImageSearchSizer.AddStretchSpacer(1)
		self.ImageSearchSizer.Add(self.ImageSearch.entry, 50, wx.ALIGN_CENTER | wx.EXPAND)

		self.ZoomControlSizer.Add(self.ZoomInButton, 10, wx.ALIGN_CENTER_VERTICAL)
		self.ZoomControlSizer.AddStretchSpacer(1)
		self.ZoomControlSizer.Add(self.ZoomOutButton, 10, wx.ALIGN_CENTER_VERTICAL)
		self.ZoomControlSizer.AddStretchSpacer(1)
		self.ZoomControlSizer.Add(self.ZoomFitButton, 10, wx.ALIGN_CENTER_VERTICAL)
		self.ZoomControlSizer.AddStretchSpacer(1)
		self.ZoomControlSizer.Add(self.ZoomActualButton, 10, wx.ALIGN_CENTER_VERTICAL)

		self.LeftPaneSizer.Add(self.ResolutionDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.Add(self.FileSizeDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.Add(self.DataSizeDisplay, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.AddStretchSpacer(3)
		self.LeftPaneSizer.Add(self.ImageQualityControl, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.AddStretchSpacer(3)
		self.LeftPaneSizer.Add(self.OutputUpdateTimer, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.AddStretchSpacer(1)
		self.LeftPaneSizer.Add(self.OutputUpdateButton, 0, wx.ALIGN_TOP | wx.ALIGN_LEFT | wx.TOP | wx.LEFT)
		self.LeftPaneSizer.AddStretchSpacer(50)
		self.LeftPaneSizer.Add(self.ZoomDisplay, 0, wx.ALIGN_CENTER_VERTICAL)
		self.LeftPaneSizer.AddStretchSpacer(1)
		self.LeftPaneSizer.Add(self.ZoomControlSizer, 0, wx.ALIGN_BOTTOM | wx.ALIGN_LEFT | wx.BOTTOM | wx.LEFT)
		self.LeftPaneSizer.AddStretchSpacer(4)
		self.LeftPaneSizer.Add(self.ImageSearchSizer, 0, wx.ALIGN_BOTTOM | wx.ALIGN_LEFT | wx.BOTTOM | wx.LEFT | wx.EXPAND)
		self.LeftPaneSizer.AddStretchSpacer(2)

		self.MainSizer.Add(self.LeftPaneSizer, 0, wx.ALIGN_LEFT | wx.LEFT | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(1)
		self.MainSizer.Add(self.image, 20, wx.ALIGN_LEFT | wx.LEFT | wx.EXPAND)
		self.SetSizer(self.MainSizer)

		self.ResolutionDisplay.SetToolTip(self.ResolutionTip)
		self.FileSizeDisplay.SetToolTip(self.FileSizeTip)
		self.DataSizeDisplay.SetToolTip(self.DataSizeTip)
		self.ImageQualityControl.SetToolTip(self.ImageQualityControlTip)
		self.OutputUpdateTimer.SetToolTip(self.OutputUpdateTimerTip)
		self.OutputUpdateButton.SetToolTip(self.OutputUpdateButtonTip)
		self.ImageQualityControl.SetItemToolTip(0, ''.join( ( 'Box Average Algorithm on Downscale, Bicubic Algorithm on Upscale', RenderThreeIfMid(' (', keybinds.get('image_quality_high_2_1'), ')') ) ) )
		self.ImageQualityControl.SetItemToolTip(1, ''.join( ( 'Bicubic Algorithm', RenderThreeIfMid(' (', keybinds.get('image_quality_high_2'), ')') ) ) )
		self.ImageQualityControl.SetItemToolTip(2, ''.join( ( 'Box Average Algorithm', RenderThreeIfMid(' (', keybinds.get('image_quality_high_1'), ')') ) ) )
		self.ImageQualityControl.SetItemToolTip(3, ''.join( ( 'Bilinear Algorithm', RenderThreeIfMid(' (', keybinds.get('image_quality_medium'), ')') ) ) )
		self.ImageQualityControl.SetItemToolTip(4, ''.join( ( 'Nearest Neighbor Algorithm', RenderThreeIfMid(' (', keybinds.get('image_quality_low'), ')') ) ) )
		self.ZoomDisplay.SetToolTip(self.ZoomDisplayTip)
		self.ZoomInButton.SetToolTip(self.ZoomInButtonTip)
		self.ZoomOutButton.SetToolTip(self.ZoomOutButtonTip)
		self.ZoomFitButton.SetToolTip(self.ZoomFitButtonTip)
		self.ZoomActualButton.SetToolTip(self.ZoomActualButtonTip)
		self.ImageSearch.entry.SetToolTip(self.ImageSearch.EntryTip)
		self.ImageSearch.LeftImage.SetToolTip(self.ImageSearch.LeftImageTip)
		self.ImageSearch.RightImage.SetToolTip(self.ImageSearch.RightImageTip)

		self.pos = CircularCounter(len(self.bitmaps.images) - 1)
		if self.image.quality == wx.IMAGE_QUALITY_HIGH:
			self.ImageQualityControl.SetSelection(0)
		elif self.image.quality == wx.IMAGE_QUALITY_BICUBIC:
			self.ImageQualityControl.SetSelection(1)
		elif self.image.quality == wx.IMAGE_QUALITY_BOX_AVERAGE:
			self.ImageQualityControl.SetSelection(2)
		elif self.image.quality == wx.IMAGE_QUALITY_BILINEAR:
			self.ImageQualityControl.SetSelection(3)
		else: # self.image.quality == wx.IMAGE_QUALITY_NEAREST
			self.ImageQualityControl.SetSelection(4)

		self.Bind( wx.EVT_BUTTON, self._OnOutputUpdateButton, id=self.OutputUpdateButton.GetId() )
		self.Bind( wx.EVT_RADIOBOX, self._OnImageQualitySelect, id=self.ImageQualityControl.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnZoomIn, id=self.ZoomInButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnZoomOut, id=self.ZoomOutButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnZoomFit, id=self.ZoomFitButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnZoomActual, id=self.ZoomActualButton.GetId() )

		pub.subscribe(self._OnFileUpdatePending, "FileUpdatePending")
		pub.subscribe(self._OnFileUpdateClear, "FileUpdateClear")
		pub.subscribe(self._OnFileUpdateTick, "FileUpdateTick")
		pub.subscribe(self._OnImageQualityLeft, "ImageQualityLeft")
		pub.subscribe(self._OnImageQualityRight, "ImageQualityRight")
		pub.subscribe(self._OnImageQualityHigh21, "ImageQualityHigh21")
		pub.subscribe(self._OnImageQualityHigh2, "ImageQualityHigh2")
		pub.subscribe(self._OnImageQualityHigh1, "ImageQualityHigh1")
		pub.subscribe(self._OnImageQualityMedium, "ImageQualityMedium")
		pub.subscribe(self._OnImageQualityLow, "ImageQualityLow")
		pub.subscribe(self._OnZoomInReceived, "ZoomIn")
		pub.subscribe(self._OnZoomOutReceived, "ZoomOut")
		pub.subscribe(self._OnZoomFitReceived, "ZoomFit")
		pub.subscribe(self._OnZoomActualReceived, "ZoomActualSize")
		pub.subscribe(self._OnIndex, "IndexImage")
		pub.subscribe(self._OnLeft, "LeftImage")
		pub.subscribe(self._OnRight, "RightImage")

		self._update()

class ImageLabel(wx.Panel):
	def _SetLabels(self):
		"Set the path label to show the path at pos in the paths array, and the index label to show pos + 1 out of length of paths array."
		self.PathEntry.SetPath( self.pos.get() )
		self.IndexEntry.SetValue( str(self.pos.get() + 1) )
		self.IndexLabel.SetLabel( ''.join( ( ' /', str(self.pos.GetMax() + 1) ) ) )
	def _OnIndexEntry(self, e):
		"Send an IndexImage message, if the index value can be converted to an Int; otherwise, reset labels."
		try:
			pub.sendMessage("IndexImage", message=int( self.IndexEntry.GetValue() ) - 1)
		except ValueError: # TODO: Should this work with any exception?
			self._SetLabels()
		e.Skip()
	def _OnIndex(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		self.pos.set(message)
		self._SetLabels()
	def _OnLeft(self, message, arg2=None):
		"Shift to the left (-1) path to the current position in the paths array if the position is greater than 0. Otherwise, loop around to the last item."
		self.pos.dec()
		self._SetLabels()
	def _OnRight(self, message, arg2=None):
		"Shift to the right (+1) path to the current position in the paths array if the position is less than the length of the paths array. Otherwise, loop around to the first item."
		self.pos.inc()
		self._SetLabels()
	def _OnFocusImageIndex(self, message, arg2=None):
		self.IndexEntry.SetFocus()
	def _OnPathEntry(self, e):
		"Send an IndexImage message, if the index of PathEntry contents can be found in paths; otherwise, try to autocomplete the contents."
		try:
			pub.sendMessage( "IndexImage", message=self.PathEntry.SearchPath( self.PathEntry.GetPath() ) )
		except ValueError: # TODO: Should this work with any exception?
			self.PathEntry.UpdateAutocomplete()
		e.Skip()
	def __init__(self, parent, paths, keybinds):
		wx.Panel.__init__(self, parent=parent)

		self.PathEntry = PathEntry(self, paths)
		self.pos = CircularCounter(self.PathEntry.GetPathsLen() - 1) # Position in paths
		self.IndexEntry = wx.TextCtrl(self, style= wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Editable display for current image index
		self.IndexLabel = wx.StaticText(self, style= wx.ALIGN_CENTER) # Static part of image index display
		self.PathEntry.EntryTip = wx.ToolTip( ''.join( ( 'Image path entry; if the path doesn\'t exist, then press enter autocomplete.', RenderThreeIfMid(' (Focus: ', keybinds.get('select_image_path'), ')'), RenderThreeIfMid(' (Open Menu: ', keybinds.get('select_image_path_menu'), ')') ) ) )
		self.IndexEntryTip = wx.ToolTip( ''.join( ( 'Image index entry. Press enter to select the image index.', RenderThreeIfMid(' (Focus: ', keybinds.get('select_image_index'), ')') ) ) )
		self.IndexLabelTip = wx.ToolTip('Total number of images.')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.PathEntry.entry.SetToolTip(self.PathEntry.EntryTip)
		self.IndexEntry.SetToolTip(self.IndexEntryTip)
		self.IndexLabel.SetToolTip(self.IndexLabelTip)

		self.sizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.PathEntry.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.PathEntry.SelfBinds()
		self.PathEntry.SelfPubSub()
		self._SetLabels()

		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		self.Bind( wx.EVT_TEXT_ENTER, self._OnPathEntry, id=self.PathEntry.entry.GetId() )
		pub.subscribe(self._OnIndex, "IndexImage")
		pub.subscribe(self._OnLeft, "LeftImage")
		pub.subscribe(self._OnRight, "RightImage")
		pub.subscribe(self._OnFocusImageIndex, "FocusImageIndex")

class ImageContainer(wx.Panel):
	def __init__(self, parent, images, ImageQuality, OutputFiles, viewport, keybinds):
		wx.Panel.__init__(self, parent=parent)

		self.image = ImagePanel(self, OutputFiles, images, ImageQuality, viewport, keybinds)
		self.label = ImageLabel(self, OutputFiles.InputPaths, keybinds)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.image, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)
