"The main windows of the software, including the entirety of the file chooser."

import os.path

import wx
import wx.lib.splitter
from pubsub import pub

from booruwizard.ui.image import ImageContainer
from booruwizard.ui.prompt import PromptContainer
from booruwizard.ui.question.main import QuestionsContainer
from booruwizard.ui.common import CircularCounter

class MainContainer(wx.lib.splitter.MultiSplitterWindow):
	def _SetSashes(self):
		"Set the sash locations to be relative to the window size."
		height = float( self.GetSize().GetHeight() )
		self.SetMinimumPaneSize( int(height * 0.1) )
		self.SetSashPosition(0, int(height * self.Sash0Pos) )
		self.SetSashPosition(1, int(height * self.Sash1Pos) )
	def _OnSizeChild(self, e):
		"Bound to EVT_SIZE to adjust sash positions based on the relative size of the panel."
		self._SetSashes()
		e.Skip()
	def _OnSashChanged(self, e):
		"Bound to EVT_SPLITTER_SASH_POS_CHANGED to record the relative locations of all sashes and set the minmum pane size."
		height = float( self.GetSize().GetHeight() )
		Sash0Pos = float( self.GetSashPosition(0) ) / height
		Sash1Pos = float( self.GetSashPosition(1) ) / height
		reset = False
		if Sash0Pos < 0.2:
			Sash0Pos = 0.2
			reset = True
		if Sash0Pos + Sash1Pos < 0.9:
			self.Sash0Pos = Sash0Pos
			self.Sash1Pos = Sash1Pos
		else:
			if Sash0Pos != self.Sash0Pos:
				self.Sash0Pos = 0.9 - Sash1Pos
			else:
				self.Sash1Pos = 0.9 - Sash0Pos
			reset = True
		if reset:
			self._SetSashes()
		e.Skip()
	def __init__(self, parent, images, ImageQuality, questions, OutputFiles, TagsTracker, ViewPort):
		wx.lib.splitter.MultiSplitterWindow.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.Sash0Pos = 0.4
		self.Sash1Pos = 0.2
		self.top = ImageContainer(self, images, ImageQuality, OutputFiles.InputPaths, ViewPort)
		self.middle = PromptContainer(self, len(OutputFiles.InputPaths), questions)
		self.bottom = QuestionsContainer(self, TagsTracker, questions, OutputFiles)

		self.SetOrientation(wx.VERTICAL)
		self.AppendWindow(self.top)
		self.AppendWindow(self.middle)
		self.AppendWindow(self.bottom)

		self.Bind( wx.EVT_SIZE, self._OnSizeChild, id=self.GetId() )
		self.Bind( wx.EVT_SPLITTER_SASH_POS_CHANGED, self._OnSashChanged, id=self.GetId() )

		size = self.GetEffectiveMinSize()
		size.SetHeight( int(float( size.GetHeight() ) * 1.9) )
		size.SetWidth( int(float( size.GetWidth() ) * 1.5) )
		self.SetMinSize(size)

class MainFrame(wx.Frame):
	def _SetTitle(self):
		"Set the title of the software with the path, its index, and the index of the current question."
		self.SetTitle(''.join( ( self.BaseTitle,
								 ' - ',
								 str(int( self.pos.get() ) + 1),
								 '/',
								 str(self.pos.GetMax() + 1),
								 ' ',
								 self.paths[self.pos.get()],
								 ' - ',
								 str(self.positions[self.pos.get()].get() + 1),
								 '/',
								 str(self.positions[self.pos.get()].GetMax() + 1)
							   )
							 )
					 )
	def _ShiftImage(self, func):
		if self.LockQuestion:
			idx = self.positions[self.pos.get()].get()
			func()
			self.positions[self.pos.get()].set(idx)
		else:
			func()
		self._SetTitle()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index to the one specified in the event, if possible."
		self._ShiftImage( lambda self=self, message=message: self.pos.set(message) )
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._ShiftImage(self.pos.dec)
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._ShiftImage(self.pos.inc)
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the event, if possible."
		self.positions[self.pos.get()].set(message)
		self._SetTitle()
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the paths array if the position is greater than 0. Otherwise, loop around to the last item."
		self.positions[self.pos.get()].dec()
		self._SetTitle()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the paths array if the position is less than the length of the paths array. Otherwise, loop around to the first item."
		self.positions[self.pos.get()].inc()
		self._SetTitle()
	def _OnLockQuestion(self, message, arg2=None):
		"Set the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = True
	def _OnUnlockQuestion(self, message, arg2=None):
		"Unset the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = False
	def _OnEmergencyExit(self, message, arg2=None):
		try:
			self.Close()
		except:
			pass
	def __init__(self, parent, BaseTitle, images, ImageQuality, questions, OutputFiles, TagsTracker, ViewPort):
		wx.Frame.__init__(self, parent=parent)

		self.BaseTitle = BaseTitle # Base window title
		self.paths = OutputFiles.InputPaths
		self.NumQuestions = len(questions)
		self.LockQuestion = False
		self.pos = CircularCounter(len(OutputFiles.InputPaths) - 1) # The position in positions
		self.positions = [CircularCounter(self.NumQuestions - 1) for p in OutputFiles.InputPaths] # The position in questions corresponding to each image
		self.main = MainContainer(self, images, ImageQuality, questions, OutputFiles, TagsTracker, ViewPort)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)
		self.WrapperSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.MainSizer.AddStretchSpacer(1)
		self.MainSizer.Add(self.main, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(1)

		self.WrapperSizer.AddStretchSpacer(1)
		self.WrapperSizer.Add(self.MainSizer, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.WrapperSizer.AddStretchSpacer(1)
		self.SetSizer(self.WrapperSizer)

		self.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		size = self.GetEffectiveMinSize()
		size.SetHeight( int(float( size.GetHeight() ) * 1.0) )
		size.SetWidth( int(float( size.GetWidth() ) * 1.25) )
		self.SetMinSize(size)
		self.SetSize( self.GetSize() ) # XXX: Windows does not automatically update the size when the minimum is set.
		self._SetTitle()

		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")
		pub.subscribe(self._OnEmergencyExit, "EmergencyExit")
		pub.subscribe(self._OnLockQuestion, "LockQuestion")
		pub.subscribe(self._OnUnlockQuestion, "UnlockQuestion")

		pub.sendMessage("StartUpdateTimer", message=None)

class FilePicker(wx.Panel):
	def GetPath(self):
		"Wrapper for self.FileChooser.GetPath"
		return self.FileChooser.GetPath()
	def __init__(self, parent, message, path):
		wx.Panel.__init__(self, parent=parent)

		self.FileLabel = wx.StaticText(self, label= message, style= wx.ALIGN_CENTER) # Static part of image index display
		#FIXME: We have to jump through these hoops, because wx.FLP_SAVE seems to be set by init, even if the style is specified; so we cannot set wx.FLP_FILE_MUST_EXIST with it
		self.FileChooser = wx.FilePickerCtrl(self, message = message, path = path, style = wx.FLP_USE_TEXTCTRL)
		self.FileChooser.SetWindowStyleFlag(wx.ALIGN_CENTER | wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
		self.FileChooser.Refresh()
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.FileLabel, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.sizer.Add(self.FileChooser, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.FileChooser.SetInitialDirectory( os.path.dirname(path) )
		self.FileChooser.SetPath(path)

class DirPicker(wx.Panel):
	def GetPath(self):
		"Wrapper for self.DirChooser.GetPath"
		return self.DirChooser.GetPath()
	def __init__(self, parent, message, path):
		wx.Panel.__init__(self, parent=parent)

		self.DirLabel = wx.StaticText(self, label= message, style= wx.ALIGN_CENTER) # Static part of image index display
		self.DirChooser = wx.DirPickerCtrl(self, message = message, path = path, style= wx.ALIGN_CENTER | wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.DirLabel, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.sizer.Add(self.DirChooser, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.DirChooser.SetInitialDirectory( os.path.dirname(path) )
		self.DirChooser.SetPath(path)

class FileDialogFrame(wx.Frame):
	def _OnOK(self, e):
		self.settings.ConfigFile = self.ConfigFileChooser.GetPath()
		self.settings.ImageInputDir = self.ImageInputDirChooser.GetPath()
		self.settings.JSONInputDir = self.JSONInputDirChooser.GetPath()
		self.settings.JSONOutputDir = self.JSONOutputDirChooser.GetPath()
		self.settings.EarlyExit = False
		self.Close()
		e.Skip()
	def _OnEmergencyExit(self, message, arg2=None):
		try:
			self.Close()
		except:
			pass
	def __init__(self, parent, APPTITLE, settings):
		wx.Frame.__init__(self, parent=parent)

		self.settings = settings
		self.ConfigFileChooser = FilePicker(self, 'Pick the config file.', settings.ConfigFile)
		self.ImageInputDirChooser = DirPicker(self, 'Pick the image directory.', settings.ImageInputDir)
		self.JSONInputDirChooser = DirPicker(self, 'Pick the JSON input directory. The image directory is used if this is blank.', settings.JSONInputDir)
		self.JSONOutputDirChooser = DirPicker(self, 'Pick the JSON output directory. The JSON input directory used if this is blank.', settings.JSONOutputDir)
		self.OKButton = wx.Button(self, label='OK')
		self.WrapperSizer  = wx.BoxSizer(wx.HORIZONTAL)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)

		self.MainSizer.AddStretchSpacer(1)
		self.MainSizer.Add(self.ConfigFileChooser, 7, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.Add(self.ImageInputDirChooser, 7, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.Add(self.JSONInputDirChooser, 7, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.Add(self.JSONOutputDirChooser, 7, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.Add(self.OKButton, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.MainSizer.AddStretchSpacer(7)

		self.WrapperSizer.AddStretchSpacer(1)
		self.WrapperSizer.Add(self.MainSizer, 40, wx.ALIGN_CENTER | wx.EXPAND)
		self.WrapperSizer.AddStretchSpacer(1)
		self.SetSizer(self.WrapperSizer)

		self.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		size = self.GetEffectiveMinSize()
		size.SetHeight( int(float( size.GetHeight() ) * 1.75) )
		size.SetWidth( int(float( size.GetWidth() ) * 1.5) )
		self.SetMinSize(size)
		self.SetSize( self.GetSize() ) # XXX: Windows does not automatically update the size when the minimum is set.
		self.SetTitle( ''.join( (APPTITLE, ' - File Chooser') ) )

		self.Bind( wx.EVT_BUTTON, self._OnOK, id=self.OKButton.GetId() )
		pub.subscribe(self._OnEmergencyExit, "EmergencyExit")
