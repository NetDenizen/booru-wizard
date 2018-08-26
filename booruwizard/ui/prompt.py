import wx
from pubsub import pub

from booruwizard.lib.tag import tag, TagsContainer
from booruwizard.lib.template import question, option, OptionQuestion, QuestionType, OptionQuestionType
from booruwizard.lib.imagereader import ManagedImage, ImageReader
from booruwizard.lib.fileops import safety, FileData, FileManager

class QuestionDisplayComponent(wx.Panel):  # This class should never be used on its own
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the event, if possible."
		if message < len(self.positions) and message >= 0:
			self.pos = message
		self._set()
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the event, if possible."
		if message < len(self.questions) and message >= 0:
			self.positions[self.pos] = message
		self._set()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		if self.pos == 0:
			self.pos = len(self.positions) - 1
		else:
			self.pos -= 1
		self._set()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		if self.pos >= len(self.positions) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._set()
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the questions array if the position is greater than 0. Otherwise, loop around to the last item."
		if self.positions[self.pos] == 0:
			self.positions[self.pos] = len(self.questions) - 1
		else:
			self.positions[self.pos] -= 1
		self._set()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the questions array if the position is less than the length of the questions array. Otherwise, loop around to the first item."
		if self.positions[self.pos] >= len(self.questions) - 1:
			self.positions[self.pos] = 0
		else:
			self.positions[self.pos] += 1
		self._set()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

class QuestionLabel(QuestionDisplayComponent):
	def _set(self):
		"Set the index label to show pos + 1 out of length of questions array."
		self.IndexEntry.SetValue( str(self.positions[self.pos] + 1) )
		self.IndexLabel.SetLabel( ''.join( ( ' /', str( len(self.questions) ) ) ) )
	def _OnIndexEntry(self, e):
		"Send a LEVT_INDEX_IMAGE event, if the index value can be converted to an Int; otherwise, reset labels."
		try:
			pub.sendMessage("IndexQuestion", message=int( self.IndexEntry.GetValue() ) - 1)
		except ValueError: # TODO: Should this work with any exception?
			self._set()
		e.Skip()
	def __init__(self, parent, NumImages, questions):
		QuestionDisplayComponent.__init__(self, parent) # TODO: Super

		self.pos = 0 # The position in positions
		self.positions = [0] * NumImages # The position in questions corresponding to each image
		self.questions = questions # Question objects
		self.IndexEntry = wx.TextCtrl(self, style= wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Editable display for current image index
		self.IndexLabel = wx.StaticText(self, style= wx.ALIGN_CENTER | wx.ST_ELLIPSIZE_END) # Static part of image index display
		self.IndexEntryTip = wx.ToolTip('Question index entry')
		self.IndexLabelTip = wx.ToolTip('Total number of questions')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.IndexEntry.SetToolTip(self.IndexEntryTip)
		self.IndexLabel.SetToolTip(self.IndexLabelTip)

		self.sizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self._set()

		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")

class QuestionPanel(QuestionDisplayComponent):
	def _set(self):
		"Set body for the question at pos."
		self.body.SetValue(self.questions[ self.positions[self.pos] ].text)
	#TODO: Roll these into a function or otherwise cleanup
	def __init__(self, parent, NumImages, questions):
		QuestionDisplayComponent.__init__(self, parent) # TODO: Super

		self.pos = 0 # The position in positions
		self.positions = [0] * NumImages # The position in questions corresponding to each image
		self.questions = questions # Question objects
		self.body = wx.TextCtrl(self, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_NOHIDESEL | wx.TE_AUTO_URL) # The body of the question #TODO: Will poor, poor Mac users get URL highlighting? Set background color?
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.body, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self._set()

		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")

class PositionButtons(wx.Panel):
	def _OnLeftImage(self, e):
		pub.sendMessage("LeftImage", message=None)
		e.Skip()
	def _OnLeftQuestion(self, e):
		pub.sendMessage("LeftQuestion", message=None)
		e.Skip()
	def _OnRightQuestion(self, e):
		pub.sendMessage("RightQuestion", message=None)
		e.Skip()
	def _OnRightImage(self, e):
		pub.sendMessage("RightImage", message=None)
		e.Skip()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

		self.LeftImage = wx.Button(self, label = '<<', style=wx.BU_EXACTFIT)
		self.LeftQuestion = wx.Button(self, label = '<', style=wx.BU_EXACTFIT)
		self.RightQuestion = wx.Button(self, label = '>', style=wx.BU_EXACTFIT)
		self.RightImage = wx.Button(self, label = '>>', style=wx.BU_EXACTFIT)
		self.LeftImageTip = wx.ToolTip('Previous image')
		self.LeftQuestionTip = wx.ToolTip('Previous question')
		self.RightImageTip = wx.ToolTip('Next image')
		self.RightQuestionTip = wx.ToolTip('Next question')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.LeftImage.SetToolTip(self.LeftImageTip)
		self.LeftQuestion.SetToolTip(self.LeftQuestionTip)
		self.RightImage.SetToolTip(self.RightImageTip)
		self.RightQuestion.SetToolTip(self.RightQuestionTip)

		self.sizer.Add(self.LeftImage, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT)
		self.sizer.Add(self.LeftQuestion, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT)
		self.sizer.Add(self.RightQuestion, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT)
		self.sizer.Add(self.RightImage, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.RIGHT)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnLeftImage, id=self.LeftImage.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnLeftQuestion, id=self.LeftQuestion.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRightQuestion, id=self.RightQuestion.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRightImage, id=self.RightImage.GetId() )

class PromptControls(wx.Panel):
	def __init__(self, parent, NumImages, questions):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

		self.label = QuestionLabel(self, NumImages, questions)
		self.buttons = PositionButtons(self)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.label, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.buttons, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

class PromptContainer(wx.Panel):
	def __init__(self, parent, NumImages, questions):
		wx.Panel.__init__(self, parent=parent) # TODO: Super

		self.prompt = QuestionPanel(self, NumImages, questions)
		self.buttons = PromptControls(self, NumImages, questions)
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.sizer.Add(self.prompt, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.ALIGN_LEFT | wx.EXPAND)
		self.sizer.Add(self.buttons, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.ALIGN_RIGHT)
		self.SetSizer(self.sizer)
