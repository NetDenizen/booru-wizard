import wx
import wx.lib.scrolledpanel
from pubsub import pub

from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import QuestionType, OptionQuestionType

class TagChoiceQuestion(wx.Panel): # This class should never be used on its own
	def _UpdateName(self, idx):
		"Update the name of a choice at the specified index, with the current number of occurrences for the related tag from the tag tracker."
		self.choices.SetString(idx,
							   ''.join( ( '[',
										  str( self.TagsTracker.ReturnStringOccurrences(self.TagNames[idx]) ),
										  '] ',
										  self.ChoiceNames[idx]
										)
									  )
							  )
	def _UpdateAllNames(self):
		for i, n in enumerate(self.ChoiceNames):
			self._UpdateName(i)
	def _UpdateChecks(self):
		"Update the name and check status of every choice."
		for i, n in enumerate(self.TagNames):
			self._UpdateName(i)
			if n and self.OutputFile.tags.ReturnStringOccurrences(n) > 0:
				self.choices.Check(i)
			else:
				self.choices.Check(i, False)
	def clear(self):
		"Clear the question for the given case."
		return
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class RadioQuestion(wx.lib.scrolledpanel.ScrolledPanel):
	def _UpdateName(self, idx):
		"Update the name of a choice at the specified index, with the current number of occurrences for the related tag from the tag tracker."
		self.choices.SetString(idx,
							   ''.join( ( '[',
										  str( self.TagsTracker.ReturnStringOccurrences(self.TagNames[idx]) ),
										  '] ',
										  self.ChoiceNames[idx]
										)
									  )
							  )
	def _UpdateAllNames(self):
		for i, n in enumerate(self.ChoiceNames):
			self._UpdateName(i)
	def _OnSelect(self, e):
		"Bound to EVT_RADIOBOX; set selected tag and remove the previously selected one."
		if self.CurrentChoice == self.choices.GetSelection():
			return
		self.OutputFile.PrepareChange()
		self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.tags.clear(self.TagNames[self.CurrentChoice], 2)
		self.OutputFile.tags.set(self.TagNames[self.choices.GetSelection()], 2)
		self.OutputFile.ClearConditionalTags(self.TagNames[self.CurrentChoice])
		self.OutputFile.SetConditionalTags(self.TagNames[self.choices.GetSelection()])
		self.OutputFile.SetTaglessTags( (self.TagNames[self.CurrentChoice],) )
		self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.FinishChange()
		self._UpdateAllNames()
		self.CurrentChoice = self.choices.GetSelection()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
		self.CurrentChoice = wx.NOT_FOUND
	def clear(self):
		"Clear the radio question for the given case."
		return
	def disp(self):
		"Display the updated radio question for the given case."
		#TODO: Should we only load choice on click, or preload choice in load?
		self.OutputFile.PrepareChange()
		self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
		Last = 0
		names = []
		for i, n in enumerate(self.TagNames):
			if n and self.OutputFile.tags.ReturnStringOccurrences(n) > 0:
				self.OutputFile.tags.clear(n, 2)
				self.OutputFile.ClearConditionalTags(n)
				Last = i
				names.append(n)
		self.choices.SetSelection(Last)
		self.OutputFile.tags.set(self.TagNames[self.choices.GetSelection()], 2)
		self.OutputFile.SetConditionalTags(self.TagNames[self.choices.GetSelection()])
		self.OutputFile.SetTaglessTags(names)
		self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.FinishChange()
		self._UpdateAllNames()
		self.CurrentChoice = self.choices.GetSelection()
	def __init__(self, parent, TagsTracker, PanelQuestion):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = PanelQuestion.GetChoiceTags() # Names of tags corresponding to each selection name
		self.ChoiceNames = PanelQuestion.GetChoiceNames() # Names of each selection
		self.CurrentChoice = wx.NOT_FOUND # Current selection in the radio box
		self.choices = wx.RadioBox(self, choices= self.ChoiceNames, style= wx.RA_SPECIFY_ROWS | wx.BORDER_NONE)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_RADIOBOX, self._OnSelect, id=self.choices.GetId() )

		self.SetOwnBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) )
		self.SetupScrolling()

class CheckQuestion(TagChoiceQuestion):
	def _UpdateChecks(self):
		"Update the name and check status of every choice."
		for i, n in enumerate(self.TagNames):
			self._UpdateName(i)
			if n and self.OutputFile.tags.ReturnStringOccurrences(n) > 0:
				self.choices.Check(i)
			else:
				self.choices.Check(i, False)
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		if e.GetInt() in self.CurrentChoices:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.clear(self.TagNames[e.GetInt()], 2)
			self.OutputFile.ClearConditionalTags(self.TagNames[e.GetInt()])
			self.OutputFile.SetTaglessTags( (self.TagNames[e.GetInt()],) )
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.remove( e.GetInt() )
		else:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.set(self.TagNames[e.GetInt()], 2)
			self.OutputFile.SetConditionalTags(self.TagNames[e.GetInt()])
			self.OutputFile.SetTaglessTags()
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.append( e.GetInt() )
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
	def disp(self):
		"Display the updated check question for the given case."
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		self.CurrentChoices = list( self.choices.GetCheckedItems() ) # Currently selected checkboxes
	def __init__(self, parent, TagsTracker, PanelQuestion):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = PanelQuestion.GetChoiceTags() # Names of tags corresponding to each selection name
		self.ChoiceNames = PanelQuestion.GetChoiceNames() # Names of each selection
		self.choices = wx.CheckListBox( self, choices= self.ChoiceNames )
		self.CurrentChoices = [] # Currently selected checkboxes
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )

class EntryBase(wx.Panel):  # This class should never be used on its own
	def load(self, OutputFile):
		"Initialize the entry question for a certain case."
		self.OutputFile = OutputFile
	def clear(self):
		"Clear the entry question for the given case."
		self._UpdateTags()
	def _OnEntry(self, e):
		"Bound to EVT_TEXT; when a space is entered, update tags."
		if self.entry.GetValue() and self.entry.GetValue()[-1].isspace(): # TODO: Handle unicode characters?
			self._UpdateTags()
		e.Skip()
	def _OnWindowDestroy(self, e):
		"Bound to EVT_WINDOW_DESTROY; update tags."
		self._UpdateTags()
		e.Skip()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class EntryQuestion(EntryBase):
	def _UpdateEntryText(self):
		"Update the current entry text according to which tags can actually be found in the output file."
		self.CurrentTags = TagsContainer()
		OldStrings = self.EntryStrings[self.pos].split()
		NewStrings = []
		self.OutputFile.lock()
		for s in OldStrings:
			if self.OutputFile.tags.ReturnStringOccurrences(s) > 0:
				NewStrings.append(s)
		self.EntryStrings[self.pos] = ' '.join(NewStrings)
		self.entry.ChangeValue(self.EntryStrings[self.pos])
		self.CurrentTags.SetStringList(NewStrings, 2)
		self.OutputFile.unlock()
	def _UpdateTags(self):
		"Subtract the previously entered tag string and add the new one"
		self.OutputFile.PrepareChange()
		self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
		if self.CurrentTags is None:
			self.CurrentTags = TagsContainer()
		names = []
		for s in self.CurrentTags.ReturnStringList(): #TODO Should this be rolled into a SetContainer function
			self.OutputFile.tags.clear(s, 2)
			self.OutputFile.ClearConditionalTags(s)
			names.append(s)
		for s in self.EntryStrings[self.pos].split():
			self.OutputFile.ClearConditionalTags(s)
		self.CurrentTags.ClearString(self.EntryStrings[self.pos], 2)
		self.CurrentTags.SetString( self.entry.GetValue(), 2 )
		for s in self.CurrentTags.ReturnStringList():
			self.OutputFile.SetConditionalTags(s)
		self.OutputFile.tags.SetContainer(self.CurrentTags)
		self.EntryStrings[self.pos] = self.entry.GetValue()
		self.OutputFile.SetTaglessTags(names)
		self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.FinishChange()
	def disp(self):
		"Display the updated entry question for the given case."
		if self.CurrentTags is None:
			self.CurrentTags = TagsContainer()
		self._UpdateEntryText()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the message, if possible."
		if 0 <= message < len(self.EntryStrings):
			self._UpdateTags()
			self.pos = message
			self._UpdateEntryText()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the entry string array if the pos is less than the length of the entry string array. Otherwise, loop around to the first item."
		self._UpdateTags()
		if self.pos >= len(self.EntryStrings) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._UpdateEntryText()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the entry string array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._UpdateTags()
		if self.pos == 0:
			self.pos = len(self.EntryStrings) - 1
		else:
			self.pos -= 1
		self._UpdateEntryText()
	def __init__(self, parent, NumImages, TagsTracker):
		EntryBase.__init__(self, parent=parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.CurrentTags = None # Keep track of the tags controlled by the entry box
		self.pos = 0 # Position in entry strings
		self.EntryStrings = [""] * NumImages # The contents of the entry boxes must be saved between images.
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.sizer.Add(self.entry, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_TEXT, self._OnEntry, id=self.entry.GetId() )
		self.Bind( wx.EVT_WINDOW_DESTROY, self._OnWindowDestroy, id=self.GetId() ) # TODO Should we bind to EVT_SET_FOCUS too?
		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")

class ImageTagsEntry(EntryBase):
	def _UpdateEntryText(self):
		"Update the current entry text according to which tags can actually be found in the output file."
		self.OutputFile.lock()
		self.entry.ChangeValue( self.OutputFile.tags.ReturnString() )
		self.CurrentString = self.OutputFile.tags.ReturnStringList()
		self.OutputFile.unlock()
	def _UpdateTags(self):
		"Subtract the previously entered tag string and add the new one"
		self.OutputFile.PrepareChange()
		self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
		for s in self.entry.GetValue().split():
			if s not in self.CurrentString:
				self.OutputFile.tags.set(s, 2)
				self.OutputFile.SetConditionalTags(s)
		for s in self.CurrentString:
			if s not in self.entry.GetValue().split():
				self.OutputFile.tags.clear(s, 2)
				self.OutputFile.ClearConditionalTags(s)
		self.CurrentString = self.entry.GetValue().split()
		self.OutputFile.SetTaglessTags( self.entry.GetValue().split() )
		self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.FinishChange()
	def disp(self):
		"Display the updated entry question for the given case."
		self._UpdateEntryText()
	def __init__(self, parent, TagsTracker):
		EntryBase.__init__(self, parent=parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.CurrentString = []

		self.sizer.Add(self.entry, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_TEXT, self._OnEntry, id=self.entry.GetId() )
		self.Bind( wx.EVT_WINDOW_DESTROY, self._OnWindowDestroy, id=self.GetId() ) # TODO Should we bind to EVT_SET_FOCUS too?

#TODO: Remove code duplication
class SessionTags(TagChoiceQuestion):
	def _OnScrollTop(self, e):
		"Prevent the widget from scrolling to the top when a box is checked."
		e.StopPropagation()
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		if e.GetInt() in self.CurrentChoices:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.clear(self.TagNames[e.GetInt()], 2)
			self.OutputFile.ClearConditionalTags(self.TagNames[e.GetInt()])
			self.OutputFile.SetTaglessTags(self.TagNames[e.GetInt()])
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.remove( e.GetInt() )
		else:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.set(self.TagNames[e.GetInt()], 2)
			self.OutputFile.SetConditionalTags(self.TagNames[e.GetInt()])
			self.OutputFile.SetTaglessTags()
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.append( e.GetInt() )
		ChoiceNames = self.TagsTracker.ReturnStringList()
		added = False
		for c in ChoiceNames:
			if c not in self.ChoiceNames:
				self.ChoiceNames.append(c)
				added = True
		if added: # TODO: Only check if there are things in ChoiceNames not in self.ChoiceNames
			self.TagNames = self.ChoiceNames
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.Unbind( wx.EVT_SCROLL_TOP, id=self.choices.GetId() )
			self.sizer.Remove(0)
			self.choices.Destroy()
			self.choices = None
			self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
			self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
			self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
			self.Bind( wx.EVT_SCROLL_TOP, self._OnScrollTop, id=self.choices.GetId() )
			self.sizer.Layout()
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		self.CurrentChoices = list( self.choices.GetCheckedItems() )
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
	def disp(self):
		"Display the updated check question for the given case."
		if self.choices is not None:
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.Unbind( wx.EVT_SCROLL_TOP, id=self.choices.GetId() )
			self.sizer.Remove(0)
			self.choices.Destroy()
			self.choices = None
		self.ChoiceNames = self.TagsTracker.ReturnStringList()
		self.TagNames = self.ChoiceNames
		self.choices = wx.CheckListBox( self, choices= self.ChoiceNames )
		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self.Bind( wx.EVT_SCROLL_TOP, self._OnScrollTop, id=self.choices.GetId() )
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		self.CurrentChoices = list( self.choices.GetCheckedItems() ) # Currently selected checkboxes
	def __init__(self, parent, TagsTracker):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = [] # Names of tags corresponding to each selection name
		self.ChoiceNames = self.TagNames # Names of each selection
		self.choices = None
		self.CurrentChoices = [] # Currently selected checkboxes
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.SetSizer(self.sizer)

class SingleStringEntry(wx.Panel): # This class should never be used on its own
	def _GetValue(self): # This determines where the field gets its value initial; define it in child classes
		"Get original value for this field."
		pass
	def _SetValue(self): # This determines where the field puts its value; define it in child classes
		"Set value controlled by this field."
		pass
	def _OnChange(self, e):
		"Set the value."
		self._SetValue()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile # File data object
	def clear(self):
		"Clear the question for the given case."
		return
	def disp(self):
		"Display the updated check question for the given case."
		self.entry.ChangeValue( self._GetValue() )
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class NameQuestion(SingleStringEntry):
	def _GetValue(self):
		"Get original value for the name field." # TODO: Should this pattern get its own function?
		self.OutputFile.lock()
		name = self.OutputFile.name
		self.OutputFile.unlock()
		if name is None:
			return ""
		else:
			return name
	def _SetValue(self):
		"Set value controlled by the name field."
		if self.checkbox.GetValue():
			self.OutputFile.PrepareChange()
			self.OutputFile.SetName( self.entry.GetValue() )
			self.OutputFile.FinishChange()
		elif self.entry.GetValue() != self.OrigValue:
			self.OutputFile.PrepareChange()
			self.OutputFile.SetName(self.OrigValue)
			self.OutputFile.FinishChange()
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile
		self.OutputFile.lock()
		self.OrigValue = self.OutputFile.name
		self.OutputFile.unlock()
	def __init__(self, parent):
		SingleStringEntry.__init__(self, parent)

		self.OutputFile = None # File data object
		self.OrigValue = None # The original value of source
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.checkbox = wx.CheckBox(self, label= 'Use this name')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.sizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.checkbox, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_TEXT, self._OnChange, id=self.entry.GetId() )
		self.Bind( wx.EVT_CHECKBOX, self._OnChange, id=self.checkbox.GetId() )

class SourceQuestion(SingleStringEntry):
	def _GetValue(self):
		"Get original value for the source field." # TODO: Should this pattern get its own function?
		self.OutputFile.lock()
		source = self.OutputFile.source
		self.OutputFile.unlock()
		if source is None:
			return ""
		else:
			return source
	def _SetValue(self):
		"Set value controlled by the source field, if the box is checked."
		if self.checkbox.GetValue():
			self.OutputFile.PrepareChange()
			self.OutputFile.SetSource( self.entry.GetValue() )
			self.OutputFile.FinishChange()
		elif self.entry.GetValue() != self.OrigValue:
			self.OutputFile.PrepareChange()
			self.OutputFile.SetSource(self.OrigValue)
			self.OutputFile.FinishChange()
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile
		self.OutputFile.lock()
		self.OrigValue = self.OutputFile.source
		self.OutputFile.unlock()
	def __init__(self, parent):
		SingleStringEntry.__init__(self, parent)

		self.OutputFile = None # File data object
		self.OrigValue = None # The original value of source
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.checkbox = wx.CheckBox(self, label= 'Use this source')
		self.sizer = wx.BoxSizer(wx.HORIZONTAL)

		self.sizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.checkbox, 0, wx.ALIGN_CENTER)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_TEXT, self._OnChange, id=self.entry.GetId() )
		self.Bind( wx.EVT_CHECKBOX, self._OnChange, id=self.checkbox.GetId() )

class SafetyQuestion(wx.lib.scrolledpanel.ScrolledPanel):
	def _UpdateSafety(self):
		"Update the current selection and set the safety to its associated enumeration."
		if self.choices.GetSelection() == self.CurrentChoice:
			pass
		else:
			self.CurrentChoice = self.choices.GetSelection()
			self.OutputFile.PrepareChange()
			self.OutputFile.rating = safety(self.CurrentChoice)
			self.OutputFile.FinishChange()
	def _OnSelect(self, e):
		"Bound to EVT_RADIOBOX; update safety."
		self._UpdateSafety()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
		self.OutputFile.lock()
		if self.OutputFile.rating is None:
			self.CurrentChoice = wx.NOT_FOUND
		else:
			self.CurrentChoice = int(self.OutputFile.rating.value)
			self.choices.SetSelection(self.CurrentChoice)
		self.OutputFile.unlock()
	def clear(self):
		"Clear the safety question for the given case."
		return
	def disp(self):
		"Display the updated check question for the given case."
		self._UpdateSafety()
	def __init__(self, parent):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent=parent)

		self.CurrentChoice = wx.NOT_FOUND
		self.OutputFile = None # File data object
		self.choices = wx.RadioBox(self, choices=('Safe', 'Questionable', 'Explicit'), style= wx.RA_SPECIFY_ROWS | wx.BORDER_NONE)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_RADIOBOX, self._OnSelect, id=self.choices.GetId() )

		self.SetOwnBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) )
		self.SetupScrolling()

class QuestionsContainer(wx.Panel):
	def _CurrentWidget(self):
		"Return the current widget."
		return self.QuestionWidgets[ self.positions[self.pos] ]
	def _disp(self):
		"Call the disp and Show functions of the current widget"
		self._CurrentWidget().disp()
		self._CurrentWidget().Show()
		self.sizer.Layout()
	def _hide(self):
		"Call the clear and Hide function of the current widget"
		self._CurrentWidget().clear()
		self._CurrentWidget().Hide()
	def _LoadAll(self):
		"Load all question widgets with the associated OutputFile"
		for w in self.QuestionWidgets:
			w.load( self.OutputFiles.ControlFiles[self.pos] )
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the message, if possible."
		if 0 <= message < len(self.positions):
			self._hide()
			self.pos = message
			self._LoadAll()
			self._disp()
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the message, if possible."
		if 0 <= message < self.NumQuestions:
			self._hide()
			self.positions[self.pos] = message
			self._disp()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._hide()
		if self.pos == 0:
			self.pos = len(self.positions) - 1
		else:
			self.pos -= 1
		self._LoadAll()
		self._disp()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._hide()
		if self.pos >= len(self.positions) - 1:
			self.pos = 0
		else:
			self.pos += 1
		self._LoadAll()
		self._disp()
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the questions array if the position is greater than 0. Otherwise, loop around to the last item."
		self._hide()
		if self.positions[self.pos] == 0:
			self.positions[self.pos] = self.NumQuestions - 1
		else:
			self.positions[self.pos] -= 1
		self._disp()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the questions array if the position is less than the length of the questions array. Otherwise, loop around to the first item."
		self._hide()
		if self.positions[self.pos] >= self.NumQuestions - 1:
			self.positions[self.pos] = 0
		else:
			self.positions[self.pos] += 1
		self._disp()
	def _OnFocusQuestionBody(self, message, arg2=None):
		self._CurrentWidget().SetFocus()
	def __init__(self, parent, TagsTracker, questions, OutputFiles):
		wx.Panel.__init__(self, parent=parent)

		self.NumQuestions = len(questions)
		self.pos = 0 # The position in positions
		self.positions = [0] * len(OutputFiles.InputPaths) # The position in questions corresponding to each image

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.OutputFiles = OutputFiles # A FileManager object
		self.QuestionWidgets = [] # wxWidgets corresponding to each question
		for q in questions:
			proportion = 0
			if q.type == OptionQuestionType.RADIO_QUESTION:
				self.QuestionWidgets.append( RadioQuestion(self, TagsTracker, q) )
				proportion = 1
			elif q.type == OptionQuestionType.CHECK_QUESTION:
				self.QuestionWidgets.append( CheckQuestion(self, TagsTracker, q) )
				proportion = 1
			elif q.type == QuestionType.ENTRY_QUESTION:
				self.QuestionWidgets.append( EntryQuestion(self, len(OutputFiles.InputPaths), TagsTracker) )
			elif q.type == QuestionType.SESSION_TAGS:
				self.QuestionWidgets.append( SessionTags(self, TagsTracker) )
				proportion = 1
			elif q.type == QuestionType.NAME_QUESTION:
				self.QuestionWidgets.append( NameQuestion(self) )
			elif q.type == QuestionType.SOURCE_QUESTION:
				self.QuestionWidgets.append( SourceQuestion(self) )
			elif q.type == QuestionType.SAFETY_QUESTION:
				self.QuestionWidgets.append( SafetyQuestion(self) )
				proportion = 1
			else: # q.type == QuestionType.IMAGE_TAGS_ENTRY:
				self.QuestionWidgets.append( ImageTagsEntry(self, TagsTracker) )
			self.sizer.Add(self.QuestionWidgets[-1], proportion, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
			self.QuestionWidgets[-1].Hide()

		self.SetSizer(self.sizer)
		self._LoadAll()
		self._disp()

		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnIndexQuestion, "IndexQuestion")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftQuestion, "LeftQuestion")
		pub.subscribe(self._OnRightQuestion, "RightQuestion")
		pub.subscribe(self._OnFocusQuestionBody, "FocusQuestionBody")
