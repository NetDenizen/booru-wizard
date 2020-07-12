"The components associated with the prompt (second from the top or middle) GUI frame."

import wx
from pubsub import pub

from booruwizard.ui.common import CircularCounter, GetPreviewText

class QuestionDisplayComponent(wx.Panel):  # This class should never be used on its own
	def _ShiftImage(self, func):
		if self.LockQuestion:
			idx = self.positions[self.pos.get()].get()
			func()
			self.positions[self.pos.get()].set(idx)
		else:
			func()
		self._set()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the event, if possible."
		self._ShiftImage( lambda self=self, message=message: self.pos.set(message) )
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the event, if possible."
		self.positions[self.pos.get()].set(message)
		self._set()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._ShiftImage(self.pos.dec)
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._ShiftImage(self.pos.inc)
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the questions array if the position is greater than 0. Otherwise, loop around to the last item."
		self.positions[self.pos.get()].dec()
		self._set()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the questions array if the position is less than the length of the questions array. Otherwise, loop around to the first item."
		self.positions[self.pos.get()].inc()
		self._set()
	def _OnLockQuestion(self, message, arg2=None):
		"Set the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = True
	def _OnUnlockQuestion(self, message, arg2=None):
		"Unset the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = False
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class QuestionSearch(wx.Panel):
	def _UpdateQuestionsMenu(self):
		"Update the questions menu, based on which question descriptions match the search terms."
		Remove = self.FieldMenu.Remove
		for i in self.FieldMenu.GetMenuItems():
			Remove(i)
		terms = tuple( t.lower().strip() for t in self.field.GetValue().split(',') )
		Append = self.FieldMenu.Append
		FieldMenuItems = self.FieldMenuItems
		for i, q in enumerate(self.questions):
			text = q.text.lower()
			for t in terms:
				if t in text:
					Append(FieldMenuItems[i])
					break
	def _OnQuestionSearch(self, e):
		self._UpdateQuestionsMenu()
		e.Skip()
	def _OnFieldEntry(self, e):
		"If there's only one matching question, change to it, otherwise, update the questions menu."
		self._UpdateQuestionsMenu()
		if len( self.FieldMenu.GetMenuItems() ) == 1:
			pub.sendMessage("IndexQuestion", message=self.FieldMenuLookup[self.FieldMenu.GetMenuItems()[0].GetId()])
		e.Skip()
	def _OnMenuItemChosen(self, e):
		"Set the question to the one chosen by the menu."
		pub.sendMessage("IndexQuestion", message=self.FieldMenuLookup[e.GetId()])
		e.Skip()
	def _OnFocusQuestionSearch(self, message, arg2=None):
		self.field.SetFocus()
	def _OnFocusQuestionSearchMenu(self, message, arg2=None):
		self.field.PopupMenu(self.FieldMenu)
	def __init__(self, parent, questions):
		wx.Panel.__init__(self, parent=parent)

		self.questions = questions
		self.FieldMenuItems = []
		self.FieldMenuLookup = {}
		self.field = wx.SearchCtrl(self, style= wx.TE_LEFT | wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL)
		self.FieldMenu = wx.Menu()
		self.FieldTip = wx.ToolTip("Search question descriptions by comma separated keywords; if only one match is found, then pressing enter loads it.")
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.field.SetToolTip(self.FieldTip)

		self.sizer.Add(self.field, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		for i, q in enumerate(questions):
			ItemId = wx.NewId()
			PreviewText = GetPreviewText(i, q.text)
			item = wx.MenuItem(self.FieldMenu, ItemId, PreviewText, PreviewText)
			self.FieldMenuItems.append(item)
			self.FieldMenuLookup[ItemId] = i
			self.Bind(wx.EVT_MENU, self._OnMenuItemChosen, id=ItemId)
		self.field.SetMenu(self.FieldMenu)
		self.field.ShowSearchButton(False)

		self.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self._OnQuestionSearch, id=self.field.GetId() )
		self.Bind( wx.EVT_TEXT_ENTER, self._OnFieldEntry, id=self.field.GetId() )
		pub.subscribe(self._OnFocusQuestionSearch, "FocusQuestionSearch")
		pub.subscribe(self._OnFocusQuestionSearchMenu, "FocusQuestionSearchMenu")

class QuestionLabel(QuestionDisplayComponent):
	def _set(self):
		"Set the index label to show pos + 1 out of length of questions array."
		self.IndexEntry.SetValue( str(self.positions[self.pos.get()].get() + 1) )
		self.IndexLabel.SetLabel( ''.join( ( ' /', str( self.positions[self.pos.get()].GetMax() + 1 ) ) ) )
	def _OnIndexEntry(self, e):
		"Send an IndexQuestion event, if the index value can be converted to an Int; otherwise, reset labels."
		try:
			pub.sendMessage("IndexQuestion", message=int( self.IndexEntry.GetValue() ) - 1)
		except ValueError:
			self._set()
		e.Skip()
	def _OnFocusQuestionIndex(self, message, arg2=None):
		self.IndexEntry.SetFocus()
	def _OnLockQuestion(self, message, arg2=None):
		QuestionDisplayComponent._OnLockQuestion(self, message, arg2=None)
		self.LockCheck.SetValue(True)
	def _OnUnlockQuestion(self, message, arg2=None):
		QuestionDisplayComponent._OnUnlockQuestion(self, message, arg2=None)
		self.LockCheck.SetValue(False)
	def _OnLockCheck(self, e):
		if self.LockCheck.GetValue():
			pub.sendMessage("LockQuestion", message=None)
		else:
			pub.sendMessage("UnlockQuestion", message=None)
	def __init__(self, parent, NumImages, questions):
		QuestionDisplayComponent.__init__(self, parent)

		self.questions = questions # Question objects
		self.LockQuestion = False
		self.pos = CircularCounter(NumImages - 1) # The position in positions
		self.positions = [CircularCounter(len(self.questions) - 1) for i in range(NumImages)] # The position in questions corresponding to each image
		self.LockCheck = wx.CheckBox(self, label= "Lock ")
		self.IndexEntry = wx.TextCtrl(self, style= wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Editable display for current image index
		self.IndexLabel = wx.StaticText(self, style= wx.ALIGN_CENTER) # Static part of image index display
		self.IndexEntryTip = wx.ToolTip('Question index entry. Press enter to select the question index.')
		self.IndexLabelTip = wx.ToolTip('Total number of questions.')
		self.LockCheckTip = wx.ToolTip('Lock all images to use the current question.')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.LockCheck.SetToolTip(self.LockCheckTip)
		self.IndexEntry.SetToolTip(self.IndexEntryTip)
		self.IndexLabel.SetToolTip(self.IndexLabelTip)

		self.sizer.Add(self.LockCheck, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.sizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self._set()

		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		self.Bind( wx.EVT_CHECKBOX, self._OnLockCheck, id=self.LockCheck.GetId() )
		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")
		pub.subscribe(self._OnFocusQuestionIndex, "FocusQuestionIndex")
		pub.subscribe(self._OnLockQuestion, "LockQuestion")
		pub.subscribe(self._OnUnlockQuestion, "UnlockQuestion")

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
	def _OnFocusQuestionBody(self, message, arg2=None):
		self._CurrentWidget().SetFocus()
	def _OnLeftImageReceived(self, message, arg2=None):
		self.LeftImage.SetFocus()
	def _OnLeftQuestionReceived(self, message, arg2=None):
		self.LeftQuestion.SetFocus()
	def _OnRightQuestionReceived(self, message, arg2=None):
		self.RightQuestion.SetFocus()
	def _OnRightImageReceived(self, message, arg2=None):
		self.RightImage.SetFocus()
	def __init__(self, parent, NumImages, NumQuestions):
		wx.Panel.__init__(self, parent=parent)

		self.LeftImage = wx.Button(self, label = '<<', style=wx.BU_EXACTFIT)
		self.LeftQuestion = wx.Button(self, label = '<', style=wx.BU_EXACTFIT)
		self.RightQuestion = wx.Button(self, label = '>', style=wx.BU_EXACTFIT)
		self.RightImage = wx.Button(self, label = '>>', style=wx.BU_EXACTFIT)
		self.LeftImageTip = wx.ToolTip('Previous image')
		self.LeftQuestionTip = wx.ToolTip('Previous question')
		self.RightImageTip = wx.ToolTip('Next image')
		self.RightQuestionTip = wx.ToolTip('Next question')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		if NumImages <= 1:
			self.LeftImage.Disable()
			self.RightImage.Disable()
		if NumQuestions <= 1:
			self.LeftQuestion.Disable()
			self.RightQuestion.Disable()

		self.LeftImage.SetToolTip(self.LeftImageTip)
		self.LeftQuestion.SetToolTip(self.LeftQuestionTip)
		self.RightImage.SetToolTip(self.RightImageTip)
		self.RightQuestion.SetToolTip(self.RightQuestionTip)

		self.sizer.Add(self.LeftImage, 10, wx.ALIGN_CENTER_VERTICAL)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.LeftQuestion, 10, wx.ALIGN_CENTER_VERTICAL)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.RightQuestion, 10, wx.ALIGN_CENTER_VERTICAL)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.RightImage, 10, wx.ALIGN_CENTER_VERTICAL)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnLeftImage, id=self.LeftImage.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnLeftQuestion, id=self.LeftQuestion.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRightQuestion, id=self.RightQuestion.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRightImage, id=self.RightImage.GetId() )

		pub.subscribe(self._OnLeftImageReceived, "LeftImage")
		pub.subscribe(self._OnLeftQuestionReceived, "LeftQuestion")
		pub.subscribe(self._OnRightQuestionReceived, "RightQuestion")
		pub.subscribe(self._OnRightImageReceived, "RightImage")

class PromptControls(wx.Panel):
	def __init__(self, parent, NumImages, questions):
		wx.Panel.__init__(self, parent=parent)

		self.search = QuestionSearch(self, questions)
		self.label = QuestionLabel(self, NumImages, questions)
		self.buttons = PositionButtons( self, NumImages, len(questions) )
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.search, 3, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.label, 3, wx.ALIGN_CENTER)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.buttons, 3, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

class QuestionPanel(QuestionDisplayComponent):
	def _set(self):
		"Set body for the question at pos."
		self.body.SetValue(self.questions[ self.positions[self.pos.get()].get() ].text)
	def _OnFocusPromptBody(self, message, arg2=None):
		self.body.SetFocus()
	def __init__(self, parent, NumImages, questions):
		QuestionDisplayComponent.__init__(self, parent)

		self.questions = questions # Question objects
		self.LockQuestion = False
		self.pos = CircularCounter(NumImages - 1) # The position in positions
		self.positions = [CircularCounter(len(self.questions) - 1) for i in range(NumImages)] # The position in questions corresponding to each image
		self.body = wx.TextCtrl(self, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_NOHIDESEL | wx.TE_AUTO_URL) # The body of the question #TODO: Will poor, poor Mac users get URL highlighting? Set background color?
		self.BodyTip = wx.ToolTip('Question prompt')
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.body.SetToolTip(self.BodyTip)

		self.sizer.Add(self.body, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.body.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		self._set()

		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")
		pub.subscribe(self._OnFocusPromptBody, "FocusPromptBody")
		pub.subscribe(self._OnLockQuestion, "LockQuestion")
		pub.subscribe(self._OnUnlockQuestion, "UnlockQuestion")

class PromptContainer(wx.Panel):
	def __init__(self, parent, NumImages, questions):
		wx.Panel.__init__(self, parent=parent)

		self.prompt = QuestionPanel(self, NumImages, questions)
		self.buttons = PromptControls(self, NumImages, questions)
		self.MainSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.WrapperSizer = wx.BoxSizer(wx.VERTICAL)

		self.MainSizer.Add(self.buttons, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.ALIGN_RIGHT)
		self.MainSizer.AddStretchSpacer(1)
		self.MainSizer.Add(self.prompt, 100, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.ALIGN_LEFT | wx.EXPAND)

		self.WrapperSizer.Add(self.MainSizer, 5, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.WrapperSizer)
