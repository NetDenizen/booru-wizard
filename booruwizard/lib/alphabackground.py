"Component to draw alternating-color boxes which represent the background of transparent images. Optimization remains a major consideration here."

from math import floor
from ctypes import c_ubyte, memmove, sizeof, byref

DEFAULT_COLOR1_PIXEL = bytearray( (153, 153, 153) )
DEFAULT_COLOR2_PIXEL = bytearray( (102, 102, 102) )
DEFAULT_SQUARE_WIDTH = 8

class TransparencyBackground:
	def __init__(self, Color1, Color2, SquareWidth):
		self.SquareWidth = SquareWidth
		self.Color1Pixel = (c_ubyte * 3)()
		self.Color2Pixel = (c_ubyte * 3)()
		#TODO: Fix kludge, if possible
		memmove(self.Color1Pixel, (c_ubyte * 3).from_buffer_copy(Color1), 3)
		memmove(self.Color2Pixel, (c_ubyte * 3).from_buffer_copy(Color2), 3)
	def _RepeatMove(self, StartOffset, dst, src, times):
		SrcLen = sizeof(src)
		offset = StartOffset
		for t in range(times):
			memmove(byref(dst, offset), src, SrcLen)
			offset += SrcLen
		return offset
	def _RenderStrip(self, width, pixel1, pixel2, square1, square2):
		SquareWidth = self.SquareWidth
		SquareLen = sizeof(square1)
		_RepeatMove = self._RepeatMove

		BytesWidth = width * 3
		strip = (c_ubyte * BytesWidth)()

		FullSquares = width // SquareWidth
		LeftoverPixels = width % SquareWidth
		StartLeftoverPixels = LeftoverPixels // 2
		EndLeftoverPixels = StartLeftoverPixels + (LeftoverPixels % 2)

		offset = _RepeatMove(0, strip, pixel1, StartLeftoverPixels)
		CurrentColor = square2
		for s in range(FullSquares):
			memmove(byref(strip, offset), CurrentColor, SquareLen)
			offset += SquareLen
			if CurrentColor == square1:
				CurrentColor = square2
			else:
				CurrentColor = square1
		if CurrentColor == square1:
			_RepeatMove(offset, strip, pixel1, EndLeftoverPixels)
		else:
			_RepeatMove(offset, strip, pixel2, EndLeftoverPixels)
		return strip
	def _RenderBlock(self, StartOffset, dst, row1, row2, rows):
		RowLen = sizeof(row1)
		offset = StartOffset
		CurrentRow = row1
		for r in range(rows):
			memmove(byref(dst, offset), CurrentRow, RowLen)
			offset += RowLen
			if CurrentRow == row2:
				CurrentRow = row1
			else:
				CurrentRow = row2
		return offset
	def _render(self, width, height):
		_RepeatMove = self._RepeatMove
		_RenderStrip = self._RenderStrip
		Color1Pixel = self.Color1Pixel
		Color2Pixel = self.Color2Pixel
		SquareWidth = self.SquareWidth

		StripSquare1 = (c_ubyte * 3 * SquareWidth)()
		StripSquare2 = (c_ubyte * 3 * SquareWidth)()
		_RepeatMove(0, StripSquare1, Color1Pixel, SquareWidth)
		_RepeatMove(0, StripSquare2, Color2Pixel, SquareWidth)

		SingleStrip1 = _RenderStrip(width, Color1Pixel, Color2Pixel, StripSquare1, StripSquare2)
		SingleStrip2 = _RenderStrip(width, Color2Pixel, Color1Pixel, StripSquare2, StripSquare1)

		RowLen = sizeof(SingleStrip1) * SquareWidth
		SingleRow1 = (c_ubyte * RowLen)()
		SingleRow2 = (c_ubyte * RowLen)()
		_RepeatMove(0, SingleRow1, SingleStrip1, SquareWidth)
		_RepeatMove(0, SingleRow2, SingleStrip2, SquareWidth)

		LeftoverPixels = height % SquareWidth
		StartLeftoverPixels = LeftoverPixels // 2
		EndLeftoverPixels = StartLeftoverPixels + (LeftoverPixels % 2)

		NumRows = (height - LeftoverPixels) // SquareWidth
		ImageLen = width * height * 3
		image = (c_ubyte * ImageLen)()

		offset = 0
		offset = _RepeatMove(offset, image, SingleStrip1, StartLeftoverPixels)
		offset = self._RenderBlock(offset, image, SingleRow2, SingleRow1, NumRows)
		if NumRows % 2 == 0:
			_RepeatMove(offset, image, SingleStrip2, EndLeftoverPixels)
		else:
			_RepeatMove(offset, image, SingleStrip1, EndLeftoverPixels)
		return bytearray(image)
	def get(self, width, height):
		return self._render( int( floor(width) ), int( floor(height) ) )
