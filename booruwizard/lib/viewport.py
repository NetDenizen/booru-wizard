from math import fabs, ceil, floor

from pubsub import pub

class ViewPort:
	def _ConstrainSample(self):
		"Ensure that the sample area remains within 0.0-1.0 bounds."
		EndXPosComp = 0.0
		EndYPosComp = 0.0
		if self.SampleXPos < 0.0:
			EndXPosComp = fabs(self.SampleXPos)
			self.SampleXPos = 0.0
		if self.SampleYPos < 0.0:
			EndYPosComp = fabs(self.SampleYPos)
			self.SampleYPos = 0.0
		EndXPos = self.SampleWidth + self.SampleXPos + EndXPosComp
		EndYPos = self.SampleHeight + self.SampleYPos + EndYPosComp
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
	def _CalcZoomTimes(self, direction, times):
		"Calculate zooming in or out a number of times."
		if self.ZoomLevel <= self.ZoomInterval:
			return
		time = floor(self.AccelSteps / times)
		ZoomIntervalIncrease = ( self.ZoomAccel * (time * time) )
		self.ZoomLevel = self.ZoomLevel + self.ZoomInterval * times * direction + ZoomIntervalIncrease
		self.ZoomInterval = self.ZoomInterval + ZoomIntervalIncrease
		self.AccelSteps += int(times * direction)
		if self.ZoomInterval <= 0.0:
			self.ZoomInterval = self.ZoomAccel
		if self.ZoomLevel <= 0.0:
			self.ZoomLevel = self.ZoomInterval
		if self.AccelSteps >= self.ZoomAccelSteps:
			self.AccelSteps = self.AccelSteps % self.ZoomAccelSteps
		elif self.AccelSteps < 0:
			self.AccelSteps = 0
	def _ApplyZoom(self, OldZoomLevel):
		"Apply zooming of an arbitrary amount."
		ZoomShift = (OldZoomLevel - self.ZoomLevel) / 2.0
		self.SampleXPos += ZoomShift
		self.SampleYPos += ZoomShift
		self.SampleWidth -= ZoomShift
		self.SampleHeight -= ZoomShift
	def ApplyZoomTimes(self, ZoomIn, times):
		"Apply zooming in or out a number of times."
		if ZoomIn:
			direction = 1.0
		else:
			direction = -1.0
		OldZoomLevel = self.ZoomLevel
		self._CalcZoomTimes(direction, times)
		self._ApplyZoom(OldZoomLevel)
		self._ConstrainSample()
	def ApplyMove(self, x, y):
		"Apply horizontal and vertical movement."
		self.SampleXPos -= x
		self.SampleYPos -= y
		self._ConstrainSample()
	def ApplyActualSize(self, image, DisplayHeight, DisplayWidth):
		#TODO: Regulate values.
		ImageSize = image.GetSize()
		OldZoomLevel = self.ZoomLevel

		self.ZoomLevel = ( ImageSize.GetWidth() * ImageSize.GetHeight() ) / (DisplayWidth * DisplayHeight)
		self.ZoomInterval = sqrt( 2 * self.ZoomAccel * (OldZoomLevel - self.ZoomLevel) + self.ZoomStartInterval * self.ZoomStartInterval )
		#if self.ZoomInterval == 0.0:
		#	self.ZoomInterval = self.ZoomAccel
		self.AccelSteps = ceil( (fabs(self.ZoomInterval - self.ZoomStartInterval) / self.ZoomAccel) * self.ZoomAccelSteps ) % self.ZoomAccelSteps

		self._ApplyZoom(OldZoomLevel)
		self._ConstrainSample()
	def ApplyFit(self):
		"Zoom so the entire area is sampled."
		self.ZoomInterval = self.ZoomStartInterval
		self.ZoomLevel = 1.0 # Current size of the sample area, relative to the actual image; always starts at 1.0
		self.AccelSteps = 0

		self.SampleXPos = 0.0 # X position of upper-left corner of sample area, as a fraction of that area's width.
		self.SampleYPos = 0.0 # Y position of upper-left corner of sample area, as a fraction of that area's height.
		self.SampleWidth = 1.0 # Width of sample area, as a fraction of the target area's full width.
		self.SampleHeight = 1.0 # Height  of sample area, as a fraction of the target area's full width.
	def view(self, image, DisplayWidth, DisplayHeight, quality):
		"Return wx.Image, through the viewport."
		ImageSize = image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()

		SampleXPos = int( floor(self.SampleXPos * ImageWidth) )
		SampleYPos = int( floor(self.SampleYPos * ImageHeight) )
		ZoomWidth = int( floor(self.SampleWidth * ImageWidth) )
		ZoomHeight = int( floor(self.SampleHeight * ImageHeight) )
		SampleRect = wx.Rect(SampleXPos, SampleYPos, ZoomWidth, ZoomHeight)

		if self.ZoomLevel > 1.0:
			NewImage = image.GetSubRect(SampleRect)
			NewImage.Rescale(DisplayWidth, DisplayHeight, quality)
		elif self.ZoomLevel == 1.0:
			if ImageWidth == DisplayWidth and ImageHeight == DisplayHeight:
				NewImage = image
			else:
				NewImage = image.Scale(DisplayWidth, DisplayHeight, quality)
		else:
			NewImage = image.Scale(floor(ImageWidth * self.ZoomLevel), floor(ImageHeight * self.ZoomLevel), quality)

		return NewImage
	def __init__(self, ZoomStartInterval, ZoomAccel, ZoomAccelSteps):
		self.ZoomStartInterval = ZoomStartInterval # Start amount ZoomLevel is increased or decreased by each zoom step.
		self.ZoomAccel = ZoomAccel # Amount ZoomInterval increases by every ZoomAccelSteps.
		self.ZoomAccelSteps = ZoomAccelSteps

		self.ApplyFit()
