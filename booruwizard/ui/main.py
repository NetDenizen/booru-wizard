import os.path

import wx
import wx.lib.splitter
from pubsub import pub

from booruwizard.lib.tag import tag, TagsContainer
from booruwizard.lib.template import question, option, OptionQuestion, QuestionType, OptionQuestionType
from booruwizard.lib.imagereader import ManagedImage, ImageReader
from booruwizard.lib.fileops import safety, FileData, FileManager

from booruwizard.ui.image import ImageContainer
from booruwizard.ui.prompt import PromptContainer
from booruwizard.ui.question import QuestionsContainer

#TODO: Class member privacy

class MainContainer(wx.lib.splitter.MultiSplitterWindow):
	def _SetSashes(self):
		"Set the sash locations to be relative to the window size."
		height = float( self.GetSize().GetHeight() )
		self.SetMinimumPaneSize( int(height * 0.1) )
		self.SetSashPosition(0, int(height * self.Sash0Pos) )
		self.SetSashPosition(1, int(height * self.Sash1Pos) )
	def _OnSize(self, e):
		"Bound to EVT_SIZE to adjust sash positions based on the relative size of the panel."
		self._SetSashes()
		e.Skip()
	def _OnSashChanged(self, e):
		"Bound to EVT_SPLITTER_SASH_POS_CHANGED to record the relative locations of all sashes and set the minmum pane size."
		height = float( self.GetSize().GetHeight() )
		Sash0Pos = float( self.GetSashPosition(0) ) / height
		Sash1Pos = float( self.GetSashPosition(1) ) / height
		if Sash0Pos + Sash1Pos < 0.9:
			self.Sash0Pos = Sash0Pos
			self.Sash1Pos = Sash1Pos
		else:
			if Sash0Pos != self.Sash0Pos:
				self.Sash0Pos = 0.9 - Sash1Pos
			else:
				self.Sash1Pos = 0.9 - Sash0Pos
			self._SetSashes()
		e.Skip()
	def __init__(self, parent, MaxBufSize, questions, OutputFiles, ConditionalTags, TagsTracker):
		wx.lib.splitter.MultiSplitterWindow.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE) # TODO: Super

		self.Sash0Pos = 0.5
		self.Sash1Pos = 0.1
		self.top = ImageContainer(self, MaxBufSize, OutputFiles.InputPaths)
		self.middle = PromptContainer(self, len(OutputFiles.InputPaths), questions)
		self.bottom = QuestionsContainer(self, ConditionalTags, TagsTracker, questions, OutputFiles)

		self.SetOrientation(wx.VERTICAL)
		self.AppendWindow(self.top)
		self.AppendWindow(self.middle)
		self.AppendWindow(self.bottom)

		self.Bind( wx.EVT_SIZE, self._OnSize, id=self.GetId() )
		self.Bind( wx.EVT_SPLITTER_SASH_POS_CHANGED, self._OnSashChanged, id=self.GetId() )

		size = self.GetEffectiveMinSize()
		size.SetHeight( int( float( size.GetHeight() ) * 2.0 ) )
		size.SetWidth( int( float( size.GetWidth() ) * 1.5 ) )
		self.SetMinSize(size)

class MainFrame(wx.Frame):
	def _SetTitle(self):
		"Set the title of the software with the path, its index, and the index of the current question."
		self.SetTitle(''.join( ( self.BaseTitle,
								 ' - ',
								 str(int(self.pos) + 1),
								 '/',
								 str( len(self.positions) ),
								 ' ',
								 self.paths[self.pos],
								 ' - ',
								 str(self.positions[self.pos] + 1),
								 '/',
								 str( self.NumQuestions )
							   )
							 )
					 )
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the event, if possible."
		if message < len(self.positions) and message >= 0:
			self.pos = message
		self._SetTitle()
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the event, if possible."
		if message < self.NumQuestions and message >= 0:
			self.positions[self.pos] = message
		self._SetTitle()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		if self.pos == 0:
			self.pos = len(self.positions) - 1
		else:
			self.pos -= 1
		self._SetTitle()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		if self.pos >= len(self.positions) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._SetTitle()
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the paths array if the position is greater than 0. Otherwise, loop around to the last item."
		if self.positions[self.pos] == 0:
			self.positions[self.pos] = self.NumQuestions - 1
		else:
			self.positions[self.pos] -= 1
		self._SetTitle()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the paths array if the position is less than the length of the paths array. Otherwise, loop around to the first item."
		if self.positions[self.pos] >= self.NumQuestions - 1:
			self.positions[self.pos] = 0
		else:
			self.positions[self.pos] += 1
		self._SetTitle()
	def _OnEmergencyExit(self, message, arg2=None):
		try:
			self.Close()
		except:
			pass
	def __init__(self, parent, BaseTitle, MaxBufSize, questions, OutputFiles, ConditionalTags, TagsTracker):
		wx.Frame.__init__(self, parent=parent) # TODO: Super

		self.BaseTitle = BaseTitle # Base window title
		self.paths = OutputFiles.InputPaths
		self.NumQuestions = len(questions)
		self.pos = 0 # The position in positions
		self.positions = [0] * len(OutputFiles.InputPaths) # The position in questions corresponding to each image
		self.main = MainContainer(self, MaxBufSize, questions, OutputFiles, ConditionalTags, TagsTracker)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.main, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		size = self.GetEffectiveMinSize()
		size.SetHeight( int( float( size.GetHeight() ) * 2.0 ) )
		size.SetWidth( int( float( size.GetWidth() ) * 1.5 ) )
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

class FilePicker(wx.Panel):
	def GetPath(self):
		"Wrapper for self.FileChooser.GetPath"
		return self.FileChooser.GetPath()
	def __init__(self, parent, message, path):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

		self.FileLabel = wx.StaticText(self, label= message, style= wx.ALIGN_CENTER) # Static part of image index display
		#TODO: We have to jump through these hoops, because wx.FLP_SAVE seems to be set by init, even if the style is specified; so we cannot set wx.FLP_FILE_MUST_EXIST with it
		self.FileChooser = wx.FilePickerCtrl(self, message = message, path = path, style = wx.FLP_USE_TEXTCTRL)
		self.FileChooser.SetWindowStyleFlag(wx.ALIGN_CENTER | wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
		self.FileChooser.Refresh()
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.FileLabel, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.sizer.Add(self.FileChooser, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.FileChooser.SetInitialDirectory( os.path.dirname(path) )

class DirPicker(wx.Panel):
	def GetPath(self):
		"Wrapper for self.DirChooser.GetPath"
		return self.DirChooser.GetPath()
	def __init__(self, parent, message, path):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

		self.DirLabel = wx.StaticText(self, label= message, style= wx.ALIGN_CENTER) # Static part of image index display
		self.DirChooser = wx.DirPickerCtrl(self, message = message, path = path, style= wx.ALIGN_CENTER | wx.DIRP_USE_TEXTCTRL | wx.DIRP_DIR_MUST_EXIST)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.DirLabel, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.sizer.Add(self.DirChooser, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.DirChooser.SetInitialDirectory( os.path.dirname(path) )

class FileDialogFrame(wx.Frame):
	def _OnOK(self, e):
		self.settings.SchemaFile = self.SchemaFileChooser.GetPath()
		self.settings.ConfigFile = self.ConfigFileChooser.GetPath()
		self.settings.InputDir = self.InputDirChooser.GetPath()
		self.settings.OutputDir = self.OutputDirChooser.GetPath()
		if not self.settings.OutputDir:
			self.settings.OutputDir = self.settings.InputDir
		self.settings.EarlyExit = False
		self.Close()
	def _OnEmergencyExit(self, message, arg2=None):
		try:
			self.Close()
		except:
			pass
	def __init__(self, parent, APPTITLE, settings):
		wx.Frame.__init__(self, parent=parent) # TODO: Super

		self.settings = settings
		self.SchemaFileChooser = FilePicker(self, 'Pick the schema file.', settings.SchemaFile)
		self.ConfigFileChooser = FilePicker(self, 'Pick the config file.', settings.ConfigFile)
		self.InputDirChooser = DirPicker(self, 'Pick the input directory.', settings.InputDir)
		self.OutputDirChooser = DirPicker(self, 'Pick the output directory. Input directory used if this is blank.', settings.OutputDir)
		self.OKButton = wx.Button(self, label='OK')
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.SchemaFileChooser, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.ConfigFileChooser, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.InputDirChooser, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.OutputDirChooser, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.Add(self.OKButton, 0, wx.ALIGN_CENTER | wx.SHAPED)
		self.SetSizer(self.sizer)

		size = self.GetEffectiveMinSize()
		size.SetHeight( int( float( size.GetHeight() ) * 2.0 ) )
		size.SetWidth( int( float( size.GetWidth() ) * 1.5 ) )
		self.SetMinSize(size)
		self.SetSize( self.GetSize() ) # XXX: Windows does not automatically update the size when the minimum is set.
		self.SetTitle( ''.join( (APPTITLE, ' - File Chooser') ) )

		self.Bind( wx.EVT_BUTTON, self._OnOK, id=self.OKButton.GetId() )
		pub.subscribe(self._OnEmergencyExit, "EmergencyExit")
