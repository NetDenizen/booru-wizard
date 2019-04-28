"Component related to adjusting display of an image."

from math import fabs, ceil, floor, sqrt
from enum import Enum

import wx

from booruwizard.lib.alphabackground import TransparencyBackground

DEFAULT_ZOOM_INTERVAL = 0.05
DEFAULT_ZOOM_ACCEL = 0.01
DEFAULT_ZOOM_ACCEL_STEPS = 2
DEFAULT_PAN_INTERVAL = 0.05

class ViewPortError(Exception):
	pass

class ViewPortState(Enum):
	FIT = 0
	ACTUAL = 1

# TODO Should actual size zooming be rounded to the nearest _CalcZoomTimes value?
class ViewPort:
	def _CalcSample(self):
		"Apply zooming of an arbitrary amount."
		#FIXME
		SizeShift = 1.0 / self.ZoomLevel
		MoveShift = (1.0 - SizeShift) / 2.0
		self.SampleXPos = self.SampleXPos - ( (1.0 - self.SampleWidth) / 2.0 ) + MoveShift
		self.SampleYPos = self.SampleYPos - ( (1.0 - self.SampleHeight) / 2.0 ) + MoveShift
		self.SampleWidth = SizeShift
		self.SampleHeight = SizeShift
	def _CalcZoomTimes(self, direction, times):
		"Calculate zooming in or out a number of times."
		if direction == -1.0 and self.ZoomLevel <= self.ZoomInterval:
			return
		AccelChange = ( (self.AccelSteps + times * direction) / self.ZoomAccelSteps )
		if AccelChange < 0.0:
			AccelChange = ceil(AccelChange)
		elif AccelChange > 0.0:
			AccelChange = floor(AccelChange)
		self.ZoomInterval += (self.ZoomAccel * AccelChange)
		if self.ZoomInterval < self.ZoomAccel:
			self.ZoomInterval = self.ZoomAccel
		self.AccelSteps += int(times * direction)
		if fabs(self.AccelSteps) >= self.ZoomAccelSteps:
			self.AccelSteps = int(self.AccelSteps % self.ZoomAccelSteps)
		ActualZoomInterval = ( (self.ZoomLevel / self.GetActualSizeRatio()[0]) * self.ZoomInterval )
		self.ZoomLevel += (ActualZoomInterval * direction)
		if self.ZoomLevel < 1.0:
			self.ZoomLevel = 1.0
	def _ConstrainSample(self):
		"Ensure that the sample area remains within 0.0-1.0 bounds."
		if self.SampleXPos < 0.0:
			self.SampleXPos = 0.0
		if self.SampleYPos < 0.0:
			self.SampleYPos = 0.0
		EndXPos = self.SampleWidth + self.SampleXPos
		EndYPos = self.SampleHeight + self.SampleYPos
		EndXPosDiff = 1.0 - EndXPos
		EndYPosDiff = 1.0 - EndYPos
		if EndXPosDiff < 0.0:
			NewSampleXPos = self.SampleXPos + EndXPosDiff
			if NewSampleXPos >= 0.0:
				self.SampleXPos = NewSampleXPos
			else:
				self.SampleXPos = 0.0
				self.SampleWidth += fabs(NewSampleXPos)
		if EndYPosDiff < 0.0:
			NewSampleYPos = self.SampleYPos + EndYPosDiff
			if NewSampleYPos >= 0.0:
				self.SampleYPos = NewSampleYPos
			else:
				self.SampleYPos = 0.0
				self.SampleHeight += fabs(NewSampleYPos)
		if self.SampleHeight > 1.0:
			self.SampleHeight = 1.0
		if self.SampleWidth > 1.0:
			self.SampleWidth = 1.0
	def ApplyZoomTimes(self, ZoomIn, times):
		"Apply zooming in or out a number of times."
		if ZoomIn:
			direction = 1.0
		else:
			direction = -1.0
		OldRatio = self.GetActualSizeRatio()[0]
		self._CalcZoomTimes(direction, times)
		self._CalcSample()
		self._ConstrainSample()
		NewRatio = self.GetActualSizeRatio()[0]
		if OldRatio != NewRatio:
			self.TotalSteps += int(times * direction)
	def ApplyMove(self, x, y):
		"Apply horizontal and vertical movement."
		self.SampleXPos += x
		self.SampleYPos += y
		self._CalcSample()
		self._ConstrainSample()
	def ApplyActualSize(self):
		#TODO: Regulate values.
		if self.image is None:
			return
		self.state = ViewPortState.ACTUAL
		self.TotalSteps = 0
		ImageSize = self.image.GetSize()

		self.ZoomLevel = sqrt( ( ImageSize.GetWidth() * ImageSize.GetHeight() ) / (self.DisplayWidth * self.DisplayHeight) )
		self.ZoomInterval = sqrt( 2 * (self.ZoomAccel / self.ZoomAccelSteps) * fabs(1.0 - self.ZoomLevel) + self.ZoomStartInterval * self.ZoomStartInterval ) #FIXME
		self.AccelSteps = int(ceil( (fabs(self.ZoomInterval - self.ZoomStartInterval) / self.ZoomAccel) * self.ZoomAccelSteps ) % self.ZoomAccelSteps)

		self._CalcSample()
		self._ConstrainSample()
	def ApplyFit(self):
		"Zoom so the entire area is sampled."
		self.state = ViewPortState.FIT
		self.TotalSteps = 0
		self.ZoomInterval = self.ZoomStartInterval
		self.ZoomLevel = 1.0 # Current size of the sample area, relative to the actual image; always starts at 1.0
		self.AccelSteps = 0

		self.SampleXPos = 0.0 # X position of upper-left corner of sample area, as a fraction of that area's width.
		self.SampleYPos = 0.0 # Y position of upper-left corner of sample area, as a fraction of that area's height.
		self.SampleWidth = 1.0 # Width of sample area, as a fraction of the target area's full width.
		self.SampleHeight = 1.0 # Height  of sample area, as a fraction of the target area's full width.
	def UpdateBackground(self, DisplayWidth, DisplayHeight):
		self.DisplayWidth = DisplayWidth
		self.DisplayHeight = DisplayHeight
		if self.BackgroundBitmap is None or\
		   self.DisplayWidth != self.BackgroundBitmap.GetWidth() or\
		   self.DisplayHeight != self.BackgroundBitmap.GetHeight():
			   self.BackgroundBitmap = wx.Bitmap.FromBuffer(self.DisplayWidth, self.DisplayHeight, self.BackgroundManager.get(self.DisplayWidth, self.DisplayHeight) )
	def UpdateImage(self, image, quality):
		"Return wx.Image, through the viewport."
		self.image = image
		if image is None:
			self.ImageBitmap = None
			return

		ImageSize = image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()

		if self.ZoomLevel > 1.0:
			SampleXPos = int( floor(self.SampleXPos * ImageWidth) )
			SampleYPos = int( floor(self.SampleYPos * ImageHeight) )
			ZoomWidth = int( floor(self.SampleWidth * ImageWidth) )
			ZoomHeight = int( floor(self.SampleHeight * ImageHeight) )
			SampleRect = wx.Rect(SampleXPos, SampleYPos, ZoomWidth, ZoomHeight)

			NewImage = image.GetSubImage(SampleRect)
			NewImage.Rescale(self.DisplayWidth, self.DisplayHeight, quality)
		elif ImageWidth == self.DisplayWidth and ImageHeight == self.DisplayHeight:
			NewImage = image
		else:
			NewImage = image.Scale(self.DisplayWidth, self.DisplayHeight, quality)

		self.ImageBitmap = wx.Bitmap(NewImage)
	def ApplyZoomSteps(self, OldSteps):
		"Zoom in or out by OldSteps, according to the state of the viewport."
		if self.TotalSteps != 0:
			return
		if self.state == ViewPortState.ACTUAL:
			self.ApplyActualSize()
			if OldSteps > 0:
				self.ApplyZoomTimes(True, OldSteps)
			elif OldSteps < 0:
				self.ApplyZoomTimes( False, abs(OldSteps) )
		else:
			self.ApplyFit()
			if OldSteps > 0:
				self.ApplyZoomTimes(True, OldSteps)
	def GetActualSizeRatio(self):
		"Return the zoom level relative to the actual size of the image, rather than the display, along with the sample and display sizes, in a tuple formatted: (ratio, SampleWidth, SampleHeight)."
		ImageSize = self.image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()
		SampleWidth = self.SampleWidth * ImageWidth
		SampleHeight = self.SampleHeight * ImageHeight
		ImageSquare = ImageWidth * ImageHeight
		return ( sqrt( ImageSquare / (SampleWidth * SampleHeight) ) /\
				 sqrt( ImageSquare / (self.DisplayWidth * self.DisplayHeight) ),
				 SampleWidth, SampleHeight )
	def GetActualFitRatio(self):
		"Return the zoom level necessary to fit the display, relative to the size of the image, rather than the display (1.0)."
		ImageSize = self.image.GetSize()
		return sqrt( (self.DisplayWidth * self.DisplayHeight) / ( ImageSize.GetWidth() * ImageSize.GetHeight() ) )
	def __init__(self, BackgroundColor1, BackgroundColor2, BackgroundSquareWidth, ZoomStartInterval, ZoomAccel, ZoomAccelSteps, PanInterval):
		self.BackgroundManager = TransparencyBackground(BackgroundColor1, BackgroundColor2, BackgroundSquareWidth)
		self.ZoomStartInterval = ZoomStartInterval # Start amount ZoomLevel is increased or decreased by each zoom step.
		self.ZoomAccel = ZoomAccel # Amount ZoomInterval increases by every ZoomAccelSteps.
		self.ZoomAccelSteps = ZoomAccelSteps
		self.PanInterval = PanInterval # Amount by which the image is panned by a single step.

		if self.ZoomStartInterval <= 0.0:
			raise ViewPortError( ''.join( ('Start zoom interval "', str(self.ZoomStartInterval), '" must be greater than 0.0') ) )
		if self.ZoomAccel <= 0.0:
			raise ViewPortError( ''.join( ('Zoom accel "', str(self.ZoomAccel), '" must be greater than 0.0') ) )
		if self.ZoomAccelSteps <= 0:
			raise ViewPortError( ''.join( ('Zoom accel steps "', str(self.ZoomAccelSteps), '" must be greater than 0') ) )
		if self.PanInterval <= 0.0:
			raise ViewPortError( ''.join( ('Pan interval "', str(self.ZoomAccelSteps), '" must be greater than 0.0') ) )

		self.DisplayWidth = 0
		self.DisplayHeight = 0
		self.BackgroundBitmap = None
		self.image = None
		self.ImageBitmap = None

		self.ApplyFit()
