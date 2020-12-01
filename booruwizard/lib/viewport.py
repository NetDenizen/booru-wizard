"Component related to adjusting display of an image."

from decimal import ROUND_FLOOR
from decimal import Decimal as D
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

class ViewPort:
	def _CalcSample(self):
		"Apply zooming of an arbitrary amount."
		PosXRatio = ( D(1.0) - (self.ZoomLevel / self.FitXLevel) )
		PosYRatio = ( D(1.0) - (self.ZoomLevel / self.FitYLevel) )
		self.SampleXPos = self.OrigSampleXPos * PosXRatio
		self.SampleYPos = self.OrigSampleYPos * PosYRatio
		self.SampleWidth = self.ZoomLevel
		self.SampleHeight = self.ZoomLevel
	def _ConstrainSample(self):
		"Ensure that the sample area remains within 0.0-1.0 bounds."
		if self.SampleXPos + self.SampleWidth > self.FitXLevel:
			self.SampleXPos = self.FitXLevel - self.SampleWidth
		if self.SampleYPos + self.SampleHeight > self.FitYLevel:
			self.SampleYPos = self.FitYLevel - self.SampleHeight
		self.SampleXPos = self.SampleXPos.max( D(0.0) )
		self.SampleYPos = self.SampleYPos.max( D(0.0) )
		if self.SampleXPos + self.SampleWidth > self.FitXLevel:
			self.SampleXPos = D(0.0)
			self.SampleWidth = self.FitXLevel
		if self.SampleYPos + self.SampleHeight > self.FitYLevel:
			self.SampleYPos = D(0.0)
			self.SampleHeight = self.FitYLevel
	def _CalcConstrainedSample(self):
		self._CalcSample()
		self._ConstrainSample()
	def _ActualFinalAccelStep(self, ZoomLevel):
		"Calculate the zoom interval necessary to reach a zoom level of 1.0, then apply that, while replacing the last step with that step."
		TargetDistance = ZoomLevel - D(1.0)
		#TODO: Ensure this is always positive
		self.ZoomLevel = D(1.0)
		if len(self.AccelStepsList) > 0 and self.AccelSteps == 0:
			self.AccelStepsList.pop()
			self.AccelStepsList.append(TargetDistance) #TODO: Make sure this is always less than zoom interval
	def MaxZoomLevel(self):
		return self.FitLevel + D(1.0)
	def ApplyZoomTimes(self, ZoomIn, times):
		"Apply zooming in or out a number of times."
		for t in range(times):
			if not ZoomIn:
				if self.ZoomLevel >= self.FitLevel:
					self.AccelSteps += 1
					if self.AccelSteps > self.ZoomAccelSteps:
						self.AccelSteps = 0
						self.ZoomInterval += self.ZoomAccel
					self.AccelStepsList.append(self.ZoomInterval)
					ZoomLevel = self.ZoomLevel
					self.ZoomLevel += self.ZoomInterval
					self.TotalSteps -= 1
					if self.ZoomLevel >= self.MaxZoomLevel():
						self.ZoomInterval = self.AccelStepsList[-2]
						self.ZoomLevel -= self.AccelStepsList[-1]
						self.AccelSteps -= 1
						self.TotalSteps += 1
						if self.AccelSteps < 0:
							self.AccelSteps = self.ZoomAccelSteps
						self.AccelStepsList.pop()
						break
				elif len(self.AccelStepsList) > 1:
						self.ZoomInterval = self.AccelStepsList[-2]
						self.ZoomLevel += self.AccelStepsList[-1]
						self.AccelSteps -= 1
						self.TotalSteps -= 1
						if self.AccelSteps < 0:
							self.AccelSteps = self.ZoomAccelSteps
						self.AccelStepsList.pop()
				else:
					break
			elif self.ZoomLevel > self.FitLevel:
				if len(self.AccelStepsList) > 1:
					if self.ZoomLevel <= self.ZoomInterval:
						if self.FitLevel < self.ZoomInterval:
							self.ZoomLevel = self.FitLevel
						else:
							self.ZoomLevel = self.ZoomInterval
						break
					self.ZoomInterval = self.AccelStepsList[-2]
					self.ZoomLevel -= self.AccelStepsList[-1]
					self.AccelSteps -= 1
					self.TotalSteps += 1
					if self.AccelSteps < 0:
						self.AccelSteps = self.ZoomAccelSteps
					self.AccelStepsList.pop()
					if self.ZoomLevel <= self.ZoomInterval:
						if self.FitLevel < self.ZoomInterval:
							self.ZoomLevel = self.FitLevel
						else:
							self.ZoomLevel = self.ZoomInterval
						break
				else:
					break
			else:
				if self.ZoomLevel <= self.ZoomInterval:
					if self.FitLevel < self.ZoomInterval:
						self.ZoomLevel = self.FitLevel
					else:
						self.ZoomLevel = self.ZoomInterval
					break
				self.AccelSteps += 1
				if self.AccelSteps > self.ZoomAccelSteps:
					self.AccelSteps = 0
					self.ZoomInterval += self.ZoomAccel
				self.AccelStepsList.append(self.ZoomInterval)
				ZoomLevel = self.ZoomLevel
				self.ZoomLevel -= self.ZoomInterval
				self.TotalSteps += 1
				if ZoomLevel > D(1.0) and self.ZoomLevel < D(1.0):
					self._ActualFinalAccelStep(ZoomLevel)
				if self.ZoomLevel <= self.ZoomInterval:
					if self.FitLevel < self.ZoomInterval:
						self.ZoomLevel = self.FitLevel
					else:
						self.ZoomLevel = self.ZoomInterval
					break
		self._CalcConstrainedSample()
	def ApplyMove(self, x, y):
		"Apply horizontal and vertical movement."
		FitMaxLevel = self.FitXLevel.max(self.FitYLevel)
		self.OrigSampleXPos += (D(x) * self.ZoomLevel * FitMaxLevel)
		self.OrigSampleYPos += (D(y) * self.ZoomLevel * FitMaxLevel)
		self.OrigSampleXPos = self.OrigSampleXPos.min(self.FitXLevel)
		self.OrigSampleYPos = self.OrigSampleYPos.min(self.FitYLevel)
		self.OrigSampleXPos = self.OrigSampleXPos.max( D(0.0) )
		self.OrigSampleYPos = self.OrigSampleYPos.max( D(0.0) )
		self._CalcConstrainedSample()
	def ApplyFit(self):
		"Zoom so the entire area is sampled."
		self.state = ViewPortState.FIT
		self.TotalSteps = 0
		self.ZoomInterval = self.ZoomStartInterval
		self.AccelSteps = 0
		if self.image is None or self.DisplayWidth == 0 or self.DisplayHeight == 0:
			self.ZoomLevel = D(1.0) # Current size of the sample area, relative to the display area; always starts at 1.0
			self.FitXLevel = self.ZoomLevel
			self.FitYLevel = self.ZoomLevel
		else:
			ImageSize = self.image.GetSize()
			self.ZoomLevel  = ( D( ImageSize.GetWidth() ) / D(self.DisplayWidth) ).max( D( ImageSize.GetHeight() ) / D(self.DisplayHeight) )
			self.FitXLevel = D( ImageSize.GetWidth() ) / D(self.DisplayWidth)
			self.FitYLevel = D( ImageSize.GetHeight() ) / D(self.DisplayHeight)

		self.OrigSampleXPos = self.FitXLevel / D(2.0) # X position of upper-left corner of sample area, as a fraction of display area's width.
		self.OrigSampleYPos = self.FitYLevel / D(2.0) # Y position of upper-left corner of sample area, as a fraction of display area's height.
		self.SampleWidth = self.ZoomLevel # Width of sample area, as a fraction of the display area's full width.
		self.SampleHeight = self.ZoomLevel # Height  of sample area, as a fraction of the display area's full width.
		self._CalcConstrainedSample()
		self.AccelStepsList = [self.ZoomInterval]
		self.FitLevel = self.ZoomLevel
	def ApplyActualSize(self):
		if self.image is None:
			return
		self.state = ViewPortState.ACTUAL

		ZoomLevel = self.ZoomLevel
		while self.ZoomLevel < D(1.0):
			self.ApplyZoomTimes(False, 1)
			if ZoomLevel == self.ZoomLevel:
				break
			else:
				ZoomLevel = self.ZoomLevel

		ZoomLevel = self.ZoomLevel
		while self.ZoomLevel > D(1.0):
			ZoomLevel = self.ZoomLevel
			self.ApplyZoomTimes(True, 1)
		if self.ZoomLevel < D(1.0):
			self._ActualFinalAccelStep(ZoomLevel)
		self.TotalSteps = 0
		self._CalcConstrainedSample()
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
	def UpdateImage(self, image, quality):
		"Return wx.Image, through the viewport."
		self.image = image
		if image is None:
			self.ImageBitmap = None
			return

		if self.ZoomLevel == self.FitLevel:
			self.state = ViewPortState.FIT
			self.TotalSteps = 0
		elif self.ZoomLevel == D(1.0):
			self.state = ViewPortState.ACTUAL
			self.TotalSteps = 0

		ImageSize = image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()

		SampleXPos = int( ( self.SampleXPos * D(self.DisplayWidth) ).quantize(D('1.'), rounding=ROUND_FLOOR) )
		SampleYPos = int( ( self.SampleYPos * D(self.DisplayHeight) ).quantize(D('1.'), rounding=ROUND_FLOOR) )
		ZoomWidth = int( ( self.SampleWidth * D(self.DisplayWidth) ).quantize(D('1.'), rounding=ROUND_FLOOR) )
		ZoomHeight = int( ( self.SampleHeight * D(self.DisplayHeight) ).quantize(D('1.'), rounding=ROUND_FLOOR) )

		self.XOffset = 0
		self.YOffset = 0
		DisplayWidth = self.DisplayWidth
		DisplayHeight = self.DisplayHeight
		if self.ZoomLevel == 1.0:
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
		elif self.ZoomLevel > self.FitLevel:
			if ImageWidth > ImageHeight:
				XAspectRatio = D(1.0)
				YAspectRatio = D(ImageHeight) / D(ImageWidth)
			else:
				YAspectRatio = D(1.0)
				XAspectRatio = D(ImageWidth) / D(ImageHeight)
			ShrinkLevel = D(1.0) - (self.ZoomLevel - self.FitLevel)
			DisplayWidth = int( ( D(DisplayWidth) * ShrinkLevel * XAspectRatio ).quantize(D('1.'), rounding=ROUND_FLOOR) )
			DisplayHeight = int( ( D(DisplayHeight) * ShrinkLevel * YAspectRatio ).quantize(D('1.'), rounding=ROUND_FLOOR) )
			self.XOffset = int( ( ( D(self.DisplayWidth) - D(DisplayWidth) ) * D(0.5) ).quantize(D('1.'), rounding=ROUND_FLOOR) )
			self.YOffset = int( ( ( D(self.DisplayHeight) - D(DisplayHeight) ) * D(0.5) ).quantize(D('1.'), rounding=ROUND_FLOOR) )

		if ZoomWidth == 0:
			ZoomWidth = 1
			SampleXPos = 0
		if ZoomHeight == 0:
			ZoomHeight = 1
			SampleYPos = 0

		SampleRect = wx.Rect(SampleXPos, SampleYPos, ZoomWidth, ZoomHeight)
		try:
			NewImage = image.GetSubImage(SampleRect)
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
		else:
			self.ApplyFit()
		if OldSteps > 0:
			self.ApplyZoomTimes(True, OldSteps)
			self.TotalSteps = OldSteps
		elif OldSteps < 0:
			self.ApplyZoomTimes( False, abs(OldSteps) )
			self.TotalSteps = OldSteps
	def GetActualSizeRatio(self):
		"Return the zoom level relative to the actual size of the image, rather than the display, along with the sample and display sizes, in a tuple formatted: (ratio, SampleWidth, SampleHeight)."
		ImageSize = self.image.GetSize()
		SampleWidth = ( self.SampleWidth * D(self.DisplayWidth) ).max( D(1) )
		SampleHeight =( self.SampleHeight * D(self.DisplayHeight) ).max( D(1) )
		ratio = self.FitLevel / self.ZoomLevel
		return (ratio, SampleWidth, SampleHeight)
	def __init__(self, BackgroundColor1, BackgroundColor2, BackgroundSquareWidth, ZoomStartInterval, ZoomAccel, ZoomAccelSteps, PanInterval):
		self.BackgroundManager = TransparencyBackground(BackgroundColor1, BackgroundColor2, BackgroundSquareWidth)
		self.ZoomStartInterval = D(ZoomStartInterval) # Start amount ZoomLevel is increased or decreased by each zoom step.
		self.ZoomAccel = D(ZoomAccel) # Amount ZoomInterval increases by every ZoomAccelSteps.
		self.ZoomAccelSteps = ZoomAccelSteps
		self.PanInterval = D(PanInterval) # Amount by which the image is panned by a single step.

		if self.ZoomStartInterval <= 0.0:
			raise ViewPortError( ''.join( ('Start zoom interval "', str(self.ZoomStartInterval), '" must be greater than 0.0') ) )
		if self.ZoomAccel <= 0.0:
			raise ViewPortError( ''.join( ('Zoom accel "', str(self.ZoomAccel), '" must be greater than 0.0') ) )
		if self.ZoomAccelSteps <= 0:
			raise ViewPortError( ''.join( ('Zoom accel steps "', str(self.ZoomAccelSteps), '" must be greater than 0') ) )
		if self.PanInterval <= D(0.0):
			raise ViewPortError( ''.join( ('Pan interval "', str(self.ZoomAccelSteps), '" must be greater than 0.0') ) )

		self.XOffset = 0
		self.YOffset = 0
		self.DisplayWidth = 0
		self.DisplayHeight = 0
		self.BackgroundBitmap = None
		self.image = None
		self.ImageBitmap = None

		self.ApplyFit()
