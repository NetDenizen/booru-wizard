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

class ViewPort:
	def _CalcSample(self):
		"Apply zooming of an arbitrary amount."
		PosXRatio = ( 1.0 - (self.ZoomLevel / self.FitXLevel) )
		PosYRatio = ( 1.0 - (self.ZoomLevel / self.FitYLevel) )
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
		self.SampleXPos = max(self.SampleXPos, 0.0)
		self.SampleYPos = max(self.SampleYPos, 0.0)
		if self.SampleXPos + self.SampleWidth > self.FitXLevel:
			self.SampleXPos = 0.0
			self.SampleWidth = self.FitXLevel
		if self.SampleYPos + self.SampleHeight > self.FitYLevel:
			self.SampleYPos = 0.0
			self.SampleHeight = self.FitYLevel
	def _CalcConstrainedSample(self):
		self._CalcSample()
		self._ConstrainSample()
	def _ActualFinalAccelStep(self, ZoomLevel):
		"Calculate the zoom interval necessary to reach a zoom level of 1.0, then apply that, while replacing the last step with that step."
		TargetDistance = ZoomLevel - 1.0
		#TODO: Ensure this is always positive
		self.ZoomLevel = 1.0
		if len(self.AccelStepsList) > 0 and self.AccelSteps == 0:
			self.AccelStepsList.pop()
			self.AccelStepsList.append(TargetDistance) #TODO: Make sure this is always less than zoom interval
	def ApplyZoomTimes(self, ZoomIn, times):
		"Apply zooming in or out a number of times."
		for t in range(times):
			if not ZoomIn:
				if self.ZoomLevel >= self.FitLevel:
					self.ZoomLevel = self.FitLevel
					break
				if len(self.AccelStepsList) > 1:
						self.ZoomInterval = self.AccelStepsList[-2]
						self.ZoomLevel += self.AccelStepsList[-1]
						self.AccelSteps -= 1
						self.TotalSteps -= 1
						if self.AccelSteps < 0:
							self.AccelSteps = self.ZoomAccelSteps
						self.AccelStepsList.pop()
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
				self.AccelStepsList.append(self.ZoomInterval)
				ZoomLevel = self.ZoomLevel
				self.ZoomLevel -= self.ZoomInterval
				self.TotalSteps += 1
				if ZoomLevel > 1.0 and self.ZoomLevel < 1.0:
					self._ActualFinalAccelStep(ZoomLevel)
		self._CalcConstrainedSample()
	def ApplyMove(self, x, y):
		"Apply horizontal and vertical movement."
		self.OrigSampleXPos += (x * self.ZoomLevel * self.FitXLevel)
		self.OrigSampleYPos += (y * self.ZoomLevel * self.FitYLevel)
		self.OrigSampleXPos = min(self.OrigSampleXPos, self.FitXLevel)
		self.OrigSampleYPos = min(self.OrigSampleYPos, self.FitYLevel)
		self.OrigSampleXPos = max(self.OrigSampleXPos, 0.0)
		self.OrigSampleYPos = max(self.OrigSampleYPos, 0.0)
		self._CalcConstrainedSample()
	def ApplyFit(self):
		"Zoom so the entire area is sampled."
		self.state = ViewPortState.FIT
		self.TotalSteps = 0
		self.ZoomInterval = self.ZoomStartInterval
		self.AccelSteps = 0
		if self.image is None or self.DisplayWidth == 0 or self.DisplayHeight == 0:
			self.ZoomLevel = 1.0 # Current size of the sample area, relative to the display area; always starts at 1.0
			self.FitXLevel = self.ZoomLevel
			self.FitYLevel = self.ZoomLevel
		else:
			ImageSize = self.image.GetSize()
			self.ZoomLevel  = max(ImageSize.GetWidth() / self.DisplayWidth, ImageSize.GetHeight() / self.DisplayHeight)
			self.FitXLevel = ImageSize.GetWidth() / self.DisplayWidth
			self.FitYLevel = ImageSize.GetHeight() / self.DisplayHeight

		self.OrigSampleXPos = self.FitXLevel / 2.0 # X position of upper-left corner of sample area, as a fraction of display area's width.
		self.OrigSampleYPos = self.FitYLevel / 2.0 # Y position of upper-left corner of sample area, as a fraction of display area's height.
		self.SampleWidth = self.ZoomLevel # Width of sample area, as a fraction of the display area's full width.
		self.SampleHeight = self.ZoomLevel # Height  of sample area, as a fraction of the display area's full width.
		self._CalcConstrainedSample()
		self.AccelStepsList = [self.ZoomInterval]
		self.FitLevel = self.ZoomLevel
	def ApplyActualSize(self):
		if self.image is None:
			return
		self.ApplyFit()
		self.state = ViewPortState.ACTUAL

		ZoomLevel = self.ZoomLevel
		while self.ZoomLevel > 1.0:
			ZoomLevel = self.ZoomLevel
			self.ApplyZoomTimes(True, 1)
		if self.ZoomLevel < 1.0:
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

		ImageSize = image.GetSize()
		ImageWidth = ImageSize.GetWidth()
		ImageHeight = ImageSize.GetHeight()

		SampleXPos = int( floor(self.SampleXPos * self.DisplayWidth) )
		SampleYPos = int( floor(self.SampleYPos * self.DisplayHeight) )
		ZoomWidth = int( floor(self.SampleWidth * self.DisplayWidth) )
		ZoomHeight = int( floor(self.SampleHeight * self.DisplayHeight) )
		SampleRect = wx.Rect(SampleXPos, SampleYPos, ZoomWidth, ZoomHeight)

		try:
			NewImage = image.GetSubImage(SampleRect)
			NewImage.Rescale(self.DisplayWidth, self.DisplayHeight, quality)

			NewImageSize = NewImage.GetSize()
			self.RenderBackground( NewImageSize.GetWidth(), NewImageSize.GetHeight() )
			self.ImageBitmap = wx.Bitmap(NewImage)
		except:
			self.ImageBitmap = None
	def ApplyZoomSteps(self, OldSteps):
		"Zoom in or out by OldSteps, according to the state of the viewport."
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
		SampleWidth = self.SampleWidth * self.DisplayWidth
		SampleHeight = self.SampleHeight * self.DisplayHeight
		if self.DisplayWidth == 0 or self.DisplayHeight == 0:
			ratio = 0
		else:
			ratio = sqrt( ( ImageSize.GetWidth() * ImageSize.GetHeight() ) / (SampleWidth * SampleHeight) )
		return (ratio, SampleWidth, SampleHeight)
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
