"Component related to adjusting display of an image."

from decimal import ROUND_FLOOR, getcontext
from decimal import Decimal as d
from enum import Enum

import wx

from booruwizard.lib.alphabackground import TransparencyBackground

DEFAULT_ZOOM_INTERVAL = 0.05
DEFAULT_ZOOM_ACCEL = 0.01
DEFAULT_ZOOM_ACCEL_STEPS = 2
DEFAULT_PAN_INTERVAL = 0.05

getcontext().prec = 17

class ViewPortError(Exception):
	pass

class ViewPortState(Enum):
	FIT = 0
	ACTUAL = 1
	ASPECT = 2

def CalcRatioDiff(ImageRatio, DisplayRatio):
	if DisplayRatio > ImageRatio:
		return ImageRatio / DisplayRatio
	else:
		return DisplayRatio / ImageRatio

def fti(value): # Floor To Int
	return int( value.quantize(d('1.'), rounding=ROUND_FLOOR) )

class ViewPort:
	def _CalcSample(self):
		"Apply zooming of an arbitrary amount."
		self.SampleXPos = self.OrigSampleXPos * (self.FitXLevel - self.SampleWidth)
		self.SampleYPos = self.OrigSampleYPos * (self.FitYLevel - self.SampleHeight)
		self.SampleWidth = self.ZoomLevel
		self.SampleHeight = self.ZoomLevel
	def _ConstrainSample(self):
		"Ensure that the sample area remains within 0.0-1.0 bounds."
		if self.SampleXPos + self.SampleWidth > self.FitXLevel:
			self.SampleXPos = self.FitXLevel - self.SampleWidth
		if self.SampleYPos + self.SampleHeight > self.FitYLevel:
			self.SampleYPos = self.FitYLevel - self.SampleHeight
		self.SampleXPos = self.SampleXPos.max( d(0.0) )
		self.SampleYPos = self.SampleYPos.max( d(0.0) )
		if self.SampleXPos + self.SampleWidth > self.FitXLevel:
			self.SampleXPos = d(0.0)
			self.SampleWidth = self.FitXLevel
		if self.SampleYPos + self.SampleHeight > self.FitYLevel:
			self.SampleYPos = d(0.0)
			self.SampleHeight = self.FitYLevel
	def _CalcConstrainedSample(self):
		self._CalcSample()
		self._ConstrainSample()
	def _ActualFinalAccelStep(self, target, ZoomLevel):
		"Calculate the zoom interval necessary to reach a zoom level of 1.0, then apply that, while replacing the last step with that step."
		TargetDistance = abs(ZoomLevel - target)
		self.ZoomLevel = target
		if len(self.ZoomLevelList) > 0:
			self.ZoomLevelList.pop()
			self.ZoomLevelList.append(self.ZoomLevel) #TODO: Make sure this is always less than zoom interval
	def ApplyZoomTimes(self, ZoomIn, times):
		"Apply zooming in or out a number of times."
		for t in range(times):
			if self.ZoomLock:
				break
			elif not ZoomIn:
				if self.ZoomLevel >= self.FitLevel:
					if self.ZoomLevel - self.FitLevel >= d(1.0):
						self.ZoomLevel = self.FitLevel + d(1.0)
						break
					self.AccelSteps += 1
					if self.AccelSteps > self.ZoomAccelSteps:
						self.AccelSteps = 0
						self.ZoomInterval += self.ZoomAccel
					self.ZoomIntervalList.append(self.ZoomInterval)
					ZoomLevel = self.ZoomLevel
					self.ZoomLevel += self.ZoomInterval
					self.ZoomLevelList.append(self.ZoomLevel)
					self.TotalSteps -= 1
					if ZoomLevel - self.FitLevel < d(1.0) and self.ZoomLevel - self.FitLevel > d(1.0):
						self.ZoomLevel = self.FitLevel + d(1.0)
						if len(self.ZoomIntervalList) > 0:
							self.ZoomIntervalList.pop()
							self.ZoomIntervalList.append(self.ZoomLevel - ZoomLevel)
						if len(self.ZoomLevelList) > 0:
							self.ZoomLevelList.pop()
							self.ZoomLevelList.append(self.ZoomLevel)
				elif len(self.ZoomIntervalList) > 0 and len(self.ZoomLevelList) > 1:
						self.ZoomInterval = self.ZoomIntervalList.pop()
						self.ZoomLevel = self.ZoomLevelList[-2]
						self.AccelSteps -= 1
						self.TotalSteps -= 1
						if self.AccelSteps < 0:
							self.AccelSteps = self.ZoomAccelSteps
						self.ZoomLevelList.pop()
				else:
					break
			elif self.ZoomLevel > self.FitLevel:
				if len(self.ZoomIntervalList) > 0 and len(self.ZoomLevelList) > 1:
						self.ZoomInterval = self.ZoomIntervalList.pop()
						self.ZoomLevel = self.ZoomLevelList[-2]
						self.AccelSteps -= 1
						self.TotalSteps += 1
						if self.AccelSteps < 0:
							self.AccelSteps = self.ZoomAccelSteps
						self.ZoomLevelList.pop()
				else:
					break
			else:
				if self.ZoomLevel <= self.ZoomInterval:
					self.ZoomLevel = self.ZoomInterval
					break
				self.AccelSteps += 1
				if self.AccelSteps > self.ZoomAccelSteps:
					self.AccelSteps = 0
					self.ZoomInterval += self.ZoomAccel
				self.ZoomIntervalList.append(self.ZoomInterval)
				ZoomLevel = self.ZoomLevel
				self.ZoomLevel -= self.ZoomInterval
				self.ZoomLevelList.append(self.ZoomLevel)
				self.TotalSteps += 1
				if ZoomLevel > d(1.0) and self.ZoomLevel < d(1.0):
					self._ActualFinalAccelStep(d(1.0), ZoomLevel)
				ZoomLevel = self.ZoomLevel
				if self.ZoomLevel <= self.ZoomInterval:
					self._ActualFinalAccelStep(self.ZoomInterval, ZoomLevel)
					break
		self._CalcConstrainedSample()
	def ApplyMove(self, x, y):
		"Apply horizontal and vertical movement."
		if self.ZoomLevel < self.FitLevel:
			self.OrigSampleXPos += d(x)
			self.OrigSampleYPos += d(y)
			self.OrigSampleXPos = self.OrigSampleXPos.min( d(1.0) )
			self.OrigSampleYPos = self.OrigSampleYPos.min( d(1.0) )
			self.OrigSampleXPos = self.OrigSampleXPos.max( d(0.0) )
			self.OrigSampleYPos = self.OrigSampleYPos.max( d(0.0) )
			self._CalcConstrainedSample()
	def ApplyMoveByPanInterval(self, x, y):
		self.ApplyMove(d(x) * self.PanInterval, d(y) * self.PanInterval)
	def ApplyFit(self):
		"Zoom so the entire area is sampled."
		self.state = ViewPortState.FIT
		self.TotalSteps = 0
		self.ZoomInterval = self.ZoomStartInterval
		self.AccelSteps = 0
		if self.image is None or self.DisplayWidth == 0 or self.DisplayHeight == 0:
			self.ZoomLevel = d(1.0) # Current size of the sample area, relative to the display area; always starts at 1.0
			self.FitXLevel = self.ZoomLevel
			self.FitYLevel = self.ZoomLevel
			self.ZoomLock = True
		else:
			ImageSize = self.image.GetSize()
			ImageWidth = ImageSize.GetWidth()
			ImageHeight = ImageSize.GetHeight()
			self.ZoomLevel  = ( d(ImageWidth) / d(self.DisplayWidth) ).max( d(ImageHeight) / d(self.DisplayHeight) )
			self.FitXLevel = d( ImageSize.GetWidth() ) / d(self.DisplayWidth)
			self.FitYLevel = d( ImageSize.GetHeight() ) / d(self.DisplayHeight)
			if ImageWidth <= self.DisplayWidth and ImageHeight <= self.DisplayHeight:
				self.ZoomLock = True
			else:
				self.ZoomLock = False

		self.OrigSampleXPos = d(0.5) # X position of upper-left corner of sample area, as a fraction of display area's width.
		self.OrigSampleYPos = d(0.5) # Y position of upper-left corner of sample area, as a fraction of display area's height.
		self.SampleWidth = self.ZoomLevel # Width of sample area, as a fraction of the display area's full width.
		self.SampleHeight = self.ZoomLevel # Height  of sample area, as a fraction of the display area's full width.
		self._CalcConstrainedSample()
		self.ZoomIntervalList = [self.ZoomInterval]
		self.ZoomLevelList = [self.ZoomLevel]
		self.FitLevel = self.ZoomLevel
	def ApplyActualSize(self):
		if self.image is None:
			return
		self.state = ViewPortState.ACTUAL

		ZoomLevel = self.ZoomLevel
		while self.ZoomLevel < d(1.0):
			self.ApplyZoomTimes(False, 1)
			if ZoomLevel == self.ZoomLevel:
				break
			else:
				ZoomLevel = self.ZoomLevel

		ZoomLevel = self.ZoomLevel
		while self.ZoomLevel > d(1.0):
			ZoomLevel = self.ZoomLevel
			self.ApplyZoomTimes(True, 1)
		if self.ZoomLevel < d(1.0):
			self._ActualFinalAccelStep(d(1.0), ZoomLevel)
		self.TotalSteps = 0
		self._CalcConstrainedSample()
	def ApplyAspect(self):
		self.ApplyFit()
		if not self.ZoomLock:
			ZoomLevel = self.ZoomLevel
			while self.ZoomLevel - self.FitLevel < d(1.0):
				self.ApplyZoomTimes(False, 1)
				if ZoomLevel == self.ZoomLevel:
					break
				else:
					ZoomLevel = self.ZoomLevel
		self.TotalSteps = 0
		self._CalcConstrainedSample()
		self.state = ViewPortState.ASPECT
	def RenderBackground(self, width, height):
		if width != 0 and height != 0 and\
		   ( self.BackgroundBitmap is None or\
		     width != self.BackgroundBitmap.GetWidth() or\
		     height != self.BackgroundBitmap.GetHeight() ):
			   self.BackgroundBitmap = wx.Bitmap.FromBuffer( width, height, self.BackgroundManager.get(width, height) )
	def UpdateBackground(self, DisplayWidth, DisplayHeight):
		self.DisplayWidth = DisplayWidth
		self.DisplayHeight = DisplayHeight
		self.RenderBackground(self.DisplayWidth, self.DisplayHeight)
	def UpdateImage(self, quality):
		"Return wx.Image, through the viewport."
		if self.image is None:
			self.ImageBitmap = None
			return

		if self.ZoomLevel == self.FitLevel:
			self.state = ViewPortState.FIT
			self.TotalSteps = 0
		elif self.ZoomLevel == d(1.0):
			self.state = ViewPortState.ACTUAL
			self.TotalSteps = 0
		elif self.ZoomLevel > self.FitLevel:
			self.state = ViewPortState.ASPECT

		ImageSize = self.image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()

		SampleXPos = fti( self.SampleXPos * d(self.DisplayWidth) )
		SampleYPos = fti( self.SampleYPos * d(self.DisplayHeight) )
		ZoomWidth = fti( self.SampleWidth * d(self.DisplayWidth) )
		ZoomHeight = fti( self.SampleHeight * d(self.DisplayHeight) )

		self.XOffset = 0
		self.YOffset = 0
		DisplayWidth = self.DisplayWidth
		DisplayHeight = self.DisplayHeight
		if self.state == ViewPortState.ASPECT:
			ZoomRatio =  d(2.0) - (self.ZoomLevel - self.FitLevel)
			if ImageWidth > ImageHeight:
				DisplayHeight = min( self.DisplayHeight, fti(CalcRatioDiff( d(ImageHeight) / d(ImageWidth), d(DisplayHeight) / d(DisplayWidth) ) * d(DisplayHeight) * ZoomRatio) )
			else:
				DisplayWidth = min( self.DisplayWidth, fti(CalcRatioDiff( d(ImageWidth) / d(ImageHeight), d(DisplayWidth) / d(DisplayHeight) ) * d(DisplayWidth) * ZoomRatio) )
			self.XOffset = fti( ( d(self.DisplayWidth) - DisplayWidth ) * d(0.5) )
			self.YOffset = fti( ( d(self.DisplayHeight) - DisplayHeight ) * d(0.5) )
		elif self.ZoomLevel == d(1.0):
			if DisplayWidth > ImageWidth:
				diff = DisplayWidth - ImageWidth
				self.XOffset = diff // 2
				DisplayWidth -= diff
				SampleXPos = max(0, SampleXPos - diff)
				ZoomWidth = ImageWidth
			if DisplayHeight > ImageHeight:
				diff = DisplayHeight - ImageHeight
				self.YOffset = diff // 2
				DisplayHeight -= diff
				SampleYPos = max(0, SampleYPos - diff)
				ZoomHeight = ImageHeight

		if ZoomWidth == 0:
			ZoomWidth = 1
			SampleXPos = 0
		if ZoomHeight == 0:
			ZoomHeight = 1
			SampleYPos = 0

		SampleRect = wx.Rect(SampleXPos, SampleYPos, ZoomWidth, ZoomHeight)
		try:
			NewImage = self.image.GetSubImage(SampleRect)
			NewImage.Rescale(DisplayWidth, DisplayHeight, quality)

			NewImageSize = NewImage.GetSize()
			self.RenderBackground( NewImageSize.GetWidth(), NewImageSize.GetHeight() )
			self.ImageBitmap = wx.Bitmap(NewImage)
		except:
			self.ImageBitmap = None
	def ApplyZoomSteps(self, OldSteps):
		"Zoom in or out by OldSteps, according to the state of the viewport."
		if self.state == ViewPortState.ACTUAL:
			OrigSampleXPos = self.OrigSampleXPos
			OrigSampleYPos = self.OrigSampleYPos
			self.ApplyFit()
			self.OrigSampleXPos = OrigSampleXPos
			self.OrigSampleYPos = OrigSampleYPos
			self.ApplyActualSize()
		elif self.state == ViewPortState.FIT:
			self.ApplyFit()
		else:
			self.ApplyAspect()
		if OldSteps > 0:
			self.ApplyZoomTimes(True, OldSteps)
			self.TotalSteps = OldSteps
		elif OldSteps < 0:
			self.ApplyZoomTimes( False, abs(OldSteps) )
			self.TotalSteps = OldSteps
	def GetActualSizeRatio(self):
		"Return the zoom level relative to the actual size of the image, rather than the display, along with the sample and display sizes, in a tuple formatted: (ratio, SampleWidth, SampleHeight)."
		SampleWidth = ( self.SampleWidth * d(self.DisplayWidth) ).max( d(1) )
		SampleHeight = ( self.SampleHeight * d(self.DisplayHeight) ).max( d(1) )
		ratio = self.FitLevel / self.ZoomLevel
		return (ratio, SampleWidth, SampleHeight)
	def CanZoomIn(self):
		return not self.ZoomLock and self.ZoomLevel > self.ZoomInterval
	def CanZoomOut(self):
		return not self.ZoomLock and self.ZoomLevel < self.FitLevel + d(1.0)
	def CanZoomAspect(self):
		return not self.ZoomLock and self.ZoomLevel - self.FitLevel != d(1.0)
	def CanZoomFit(self):
		return self.ZoomLevel != self.FitLevel
	def CanZoomActual(self):
		return self.ZoomLevel != d(1.0)
	def __init__(self, BackgroundColor1, BackgroundColor2, BackgroundSquareWidth, ZoomStartInterval, ZoomAccel, ZoomAccelSteps, PanInterval):
		self.BackgroundManager = TransparencyBackground(BackgroundColor1, BackgroundColor2, BackgroundSquareWidth)
		self.ZoomStartInterval = d(ZoomStartInterval) # Start amount ZoomLevel is increased or decreased by each zoom step.
		self.ZoomAccel = d(ZoomAccel) # Amount ZoomInterval increases by every ZoomAccelSteps.
		self.ZoomAccelSteps = ZoomAccelSteps
		self.PanInterval = d(PanInterval) # Amount by which the image is panned by a single step.

		if self.ZoomStartInterval <= d(0.0):
			raise ViewPortError( ''.join( ('Start zoom interval "', str(self.ZoomStartInterval), '" must be greater than 0.0') ) )
		if self.ZoomAccel <= d(0.0):
			raise ViewPortError( ''.join( ('Zoom accel "', str(self.ZoomAccel), '" must be greater than 0.0') ) )
		if self.ZoomAccelSteps <= 0:
			raise ViewPortError( ''.join( ('Zoom accel steps "', str(self.ZoomAccelSteps), '" must be greater than 0') ) )
		if self.PanInterval <= d(0.0):
			raise ViewPortError( ''.join( ('Pan interval "', str(self.ZoomAccelSteps), '" must be greater than 0.0') ) )

		self.XOffset = 0
		self.YOffset = 0
		self.DisplayWidth = 0
		self.DisplayHeight = 0
		self.BackgroundBitmap = None
		self.image = None
		self.ImageBitmap = None

		self.ApplyFit()
