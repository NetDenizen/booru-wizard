"The components associated with the question (third from the top) GUI frame."

import re
from sys import platform

import wx
import wx.lib.scrolledpanel
from pubsub import pub

from kanji_to_romaji import kanji_to_romaji

from booruwizard.lib.fileops import safety
from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import QuestionType, OptionQuestionType
from booruwizard.ui.common import CircularCounter

RE_NOT_WHITESPACE = re.compile(r'\S+')
RE_WHITESPACE = re.compile(r'\s')

class TagChoiceQuestion(wx.Panel): # This class should never be used on its own
	def _UpdateChoice(self, choice):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		if choice in self.CurrentChoices:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.clear(self.TagNames[choice], 2)
			self.OutputFile.ClearConditionalTags(self.TagNames[choice])
			self.OutputFile.SetTaglessTags( (self.TagNames[choice],) )
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.remove(choice)
		else:
			self.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.tags.set(self.TagNames[choice], 2)
			self.OutputFile.SetConditionalTags(self.TagNames[choice])
			self.OutputFile.SetTaglessTags()
			self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
			self.OutputFile.FinishChange()
			self.CurrentChoices.append(choice)
	def _UpdateName(self, idx):
		"Update the name of a choice at the specified index, with the current number of occurrences for the related tag from the tag tracker."
		TagName = self.TagNames[idx]
		occurrences = self.OutputFile.tags.ReturnStringOccurrences(TagName)
		if occurrences == 2:
			status = '[user] '
		elif occurrences == 1:
			status = '[auto] '
		else:
			status = '[none] '
		self.choices.SetString(idx,
							   ''.join( ( '[',
										  str( self.TagsTracker.ReturnStringOccurrences(TagName) ),
										  '] ',
										  status,
										  self.ChoiceNames[idx]
										)
									  )
							  )
	def _UpdateAllNames(self):
		for i, n in enumerate(self.ChoiceNames):
			self._UpdateName(i)
	def _UpdateChecks(self):
		"Update the name and check status of every choice."
		# TODO: Should the choices be chosen in a different procedure?
		self.CurrentChoices = []
		for i, n in enumerate(self.TagNames):
			self._UpdateName(i)
			occurrences = self.OutputFile.tags.ReturnStringOccurrences(n)
			if n and occurrences > 0:
				if occurrences == 2:
					self.CurrentChoices.append(i)
				self.choices.Check(i)
			else:
				self.choices.Check(i, False)
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
	def clear(self):
		"Clear the question for the given case."
		pass
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class RadioQuestion(wx.lib.scrolledpanel.ScrolledPanel):
	def _UpdateName(self, idx):
		"Update the name of a choice at the specified index, with the current number of occurrences for the related tag from the tag tracker."
		TagName = self.TagNames[idx]
		occurrences = self.OutputFile.tags.ReturnStringOccurrences(TagName)
		if occurrences == 2:
			status = '[user] '
		elif occurrences == 1:
			status = '[auto] '
		else:
			status = '[none] '
		self.choices.SetString(idx,
							   ''.join( ( '[',
										  str( self.TagsTracker.ReturnStringOccurrences(TagName) ),
										  '] ',
										  status,
										  self.ChoiceNames[idx]
										)
									  )
							  )
	def _UpdateAllNames(self):
		for i, n in enumerate(self.ChoiceNames):
			self._UpdateName(i)
	def _OnSelect(self, e):
		"Bound to EVT_RADIOBOX; set selected tag and remove the previously selected one."
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
		pass
	def disp(self):
		"Display the updated radio question for the given case."
		self.OutputFile.PrepareChange()
		self.TagsTracker.SubStringList(self.OutputFile.tags.ReturnStringList(), 1)
		Last = 0
		LastOccurrences = 0
		names = []
		for i, n in enumerate(self.TagNames):
			if not n:
				continue
			occurrences = self.OutputFile.tags.ReturnStringOccurrences(n)
			if occurrences > LastOccurrences:
				self.OutputFile.tags.clear(n, 2)
				self.OutputFile.ClearConditionalTags(n)
				Last = i
				LastOccurrences = occurrences
				names.append(n)
		self.choices.SetSelection(Last)
		self.OutputFile.tags.set(self.TagNames[self.choices.GetSelection()], LastOccurrences)
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
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		self._UpdateChoice( e.GetInt() )
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		e.Skip()
	def disp(self):
		"Display the updated check question for the given case."
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
	def __init__(self, parent, TagsTracker, PanelQuestion):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = PanelQuestion.GetChoiceTags() # Names of tags corresponding to each selection name
		self.ChoiceNames = PanelQuestion.GetChoiceNames() # Names of each selection
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
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
	def _OnUpdateEvent(self, e):
		"Generic event handler, to update tags based on the contents of the field."
		self._UpdateTags()
		e.Skip()
	def _OnRomanize(self, e):
		"Replace Kana characters of selected parts of the string with their Romaji equivalents, using kanji_to_romaj, and update the tags accordingly."
		text = self.entry.GetValue()
		indices = list( self.entry.GetSelection() )
		if indices[0] == indices[1]:
			indices[0] = 0
			indices[1] = len(text)
		StartText = text[ :indices[0] ]
		EndText = text[ indices[1]: ]
		#XXX: Platform specific code. There appears to be a discrepancy between how the string is stored in memory (with Unix-style line endings), and how it is represented by the TextCtrl buffer in Windows (Windows line endings). The latter is used by GetSelection, so we alter the string to accurately reflect it in Windows.
		if platform == 'win32':
			text = text.replace('\r\n', '\n').replace('\n', '\r\n')
		text = text[ indices[0]:indices[1] ]
		TagStrings = []
		start = 0
		found = RE_WHITESPACE.search(text[start:])
		while found is not None:
			end = start + found.start(0) + len( found.group(0) )
			TagStrings.append(text[start:end])
			start = end
			found = RE_WHITESPACE.search(text[start:])
		TagStrings.append(text[start:])
		OutputStrings = [StartText]
		for s in TagStrings:
			left = ''
			middle = ''
			right = ''
			if len(s) != len( s.lstrip() ):
				left = s[:len(s) - len( s.lstrip() )]
			if s.strip() != '':
				middle = kanji_to_romaji( s.strip() ).replace(' ', '_')
			if len(s) != len( s.rstrip() ) and s.lstrip() != s.rstrip():
				right = s[len( s.rstrip() ):]
			OutputStrings.append(left)
			OutputStrings.append(middle)
			OutputStrings.append(right)
		OutputStrings.append(EndText)
		self.entry.ChangeValue( ''.join(OutputStrings) )
		self._UpdateTags()
		e.Skip()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class EntryQuestion(EntryBase):
	def _UpdateEntryText(self):
		"Update the current entry text according to which tags can actually be found in the output file."
		self.CurrentTags = TagsContainer()
		OldStrings = []
		OldTags = []
		SpaceStart = 0
		while(True):
			found = RE_NOT_WHITESPACE.search(self.EntryStrings[self.pos.get()][SpaceStart:])
			if found is None:
				break
			StringStart = SpaceStart + found.start(0)
			StringEnd = StringStart + len( found.group(0) )
			OldStrings.append(self.EntryStrings[self.pos.get()][SpaceStart:StringStart])
			OldTags.append(self.EntryStrings[self.pos.get()][StringStart:StringEnd])
			OldStrings.append(self.EntryStrings[self.pos.get()][StringStart:StringEnd])
			SpaceStart = StringEnd
		FinalSpace = self.EntryStrings[self.pos.get()][SpaceStart:]
		NewStrings = []
		NewStringsStripped = []
		self.OutputFile.lock()
		for s in OldStrings:
			if s not in OldTags or self.OutputFile.tags.ReturnStringOccurrences( s.strip() ) > 0:
				NewStrings.append(s)
				NewStringsStripped.append( s.strip() )
		NewStrings.append(FinalSpace)
		self.EntryStrings[self.pos.get()] = ''.join(NewStrings)
		self.entry.ChangeValue(self.EntryStrings[self.pos.get()])
		self.CurrentTags.SetStringList(NewStringsStripped, 2)
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
		for s in self.EntryStrings[self.pos.get()].split():
			self.OutputFile.ClearConditionalTags(s)
		self.CurrentTags.ClearString(self.EntryStrings[self.pos.get()], 2)
		self.CurrentTags.SetString(self.entry.GetValue(), 2)
		for s in self.CurrentTags.ReturnStringList():
			self.OutputFile.SetConditionalTags(s)
		self.OutputFile.tags.SetContainer(self.CurrentTags)
		self.EntryStrings[self.pos.get()] = self.entry.GetValue()
		self.OutputFile.SetTaglessTags(names)
		self.TagsTracker.AddStringList(self.OutputFile.tags.ReturnStringList(), 1)
		self.OutputFile.FinishChange()
	def clear(self):
		"Clear the entry question for the given case."
		pass
	def disp(self):
		"Display the updated entry question for the given case."
		if self.CurrentTags is None:
			self.CurrentTags = TagsContainer()
		self._UpdateEntryText()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the message, if possible."
		self._UpdateTags()
		self.pos.set(message)
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the entry string array if the pos is less than the length of the entry string array. Otherwise, loop around to the first item."
		self._UpdateTags()
		self.pos.inc()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the entry string array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._UpdateTags()
		self.pos.dec()
	def __init__(self, parent, NumImages, TagsTracker):
		EntryBase.__init__(self, parent=parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.CurrentTags = None # Keep track of the tags controlled by the entry box
		self.pos = CircularCounter(NumImages) # Position in entry strings
		self.EntryStrings = [""] * NumImages # The contents of the entry boxes must be saved between images.
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)

		self.sizer.Add(self.entry, 55, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnUpdateEvent, id=self.entry.GetId() )
		self.Bind( wx.EVT_WINDOW_DESTROY, self._OnUpdateEvent, id=self.GetId() ) # TODO Should we bind to EVT_SET_FOCUS too?
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
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.CurrentString = []

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)

		self.sizer.Add(self.entry, 55, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnUpdateEvent, id=self.entry.GetId() )
		self.Bind( wx.EVT_WINDOW_DESTROY, self._OnUpdateEvent, id=self.GetId() ) # TODO Should we bind to EVT_SET_FOCUS too?

class SessionTags(TagChoiceQuestion):
	def _MakeNames(self):
		RawNames = self.TagsTracker.ReturnStringList()
		UserNames = []
		AutoNames = []
		NoneNames = []
		for n in RawNames:
			occurrences = self.OutputFile.tags.ReturnStringOccurrences(n)
			if occurrences == 2:
				UserNames.append(n)
			elif occurrences == 1:
				AutoNames.append(n)
			else:
				NoneNames.append(n)
		output = []
		output.extend(UserNames)
		output.extend(AutoNames)
		output.extend(NoneNames)
		return output
	def _OnScrollTop(self, e):
		"Prevent the widget from scrolling to the top when a box is checked."
		e.StopPropagation()
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		self._UpdateChoice( e.GetInt() )
		ChoiceNames = self._MakeNames()
		added = False
		for c in ChoiceNames:
			if c not in self.ChoiceNames:
				self.ChoiceNames.append(c)
				added = True
		if added:
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
		e.Skip()
	def disp(self):
		"Display the updated check question for the given case."
		if self.choices is not None:
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.Unbind( wx.EVT_SCROLL_TOP, id=self.choices.GetId() )
			self.sizer.Remove(0)
			self.choices.Destroy()
			self.choices = None
		self.ChoiceNames = self._MakeNames()
		self.TagNames = self.ChoiceNames
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self.Bind( wx.EVT_SCROLL_TOP, self._OnScrollTop, id=self.choices.GetId() )
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
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

class ImageTagsList(TagChoiceQuestion): # This class should never be used on its own
	def _SetIndex(self):
		self.IndexLabel.SetLabel( ''.join( ( ' /', str( len(self.OutputFiles) ) ) ) )
		self.IndexEntry.SetValue( str(self.CurrentSource.get() + 1) )
	def _MakeNames(self):
		RawNames = self.OutputFile.tags.ReturnStringList()
		UserNames = []
		AutoNames = []
		for n in RawNames:
			if self.parent.OwnTags.OutputFile.tags.ReturnStringOccurrences(n) > 0:
				continue
			occurrences = self.OutputFile.tags.ReturnStringOccurrences(n)
			if occurrences == 2:
				UserNames.append(n)
			elif occurrences == 1:
				AutoNames.append(n)
		output = []
		output.extend(UserNames)
		output.extend(AutoNames)
		return output
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; add or remove the selected or unselected choice to or from CurrentChoices."
		if e.GetInt() in self.CurrentChoices:
			self.CurrentChoices.remove( e.GetInt() )
		else:
			self.CurrentChoices.append( e.GetInt() )
		e.Skip()
	def _OnIndexEntry(self, e):
		"Switch the OutputFile selected by the value of the index entry, or reset to the last valid one."
		value = int( self.IndexEntry.GetValue() ) - 1
		success = self.CurrentSource.set(value)
		if success:
			self.OutputFile = self.OutputFiles[value]
			self.disp()
		else:
			self._SetIndex()
		e.Skip()
	def _OnLeft(self, e):
		"Shift to the left (-1) image to the current position in the OutputFiles array, if the position is greater than 0. Otherwise, loop around to the last item. Then, load the relevant file."
		self.CurrentSource.dec()
		self.OutputFile = self.OutputFiles[self.CurrentSource.get()]
		self.disp()
		e.Skip()
	def _OnRight(self, e):
		"Shift to the right (+1) image to the current position in the output files array if the position is less than the length of the output files array. Otherwise, loop around to the last item. Then, load the relevant file."
		self.CurrentSource.inc()
		self.OutputFile = self.OutputFiles[self.CurrentSource.get()]
		self.disp()
		e.Skip()
	def _OnCommit(self, e):
		"Copy the selected tags to the output SessionTags field of the parent class."
		for c in self.CurrentChoices:
			self.parent.OwnTags.OutputFile.PrepareChange()
			self.TagsTracker.SubStringList(self.parent.OwnTags.OutputFile.tags.ReturnStringList(), 1)
			self.parent.OwnTags.OutputFile.tags.set( self.TagNames[c],
													 self.OutputFile.tags.ReturnStringOccurrences(self.TagNames[c])
												   )
			self.TagsTracker.AddStringList(self.parent.OwnTags.OutputFile.tags.ReturnStringList(), 1)
			self.parent.OwnTags.OutputFile.FinishChange()
		self.parent.disp()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		pass
	def disp(self):
		"Display the updated question for the given case."
		if self.choices is not None:
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.sizer.Remove(2)
			self.choices.Destroy()
			self.choices = None
		self.ChoiceNames = self._MakeNames()
		self.TagNames = self.ChoiceNames
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
		self.sizer.Add(self.choices, 100, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self.OutputFile.lock()
		self._UpdateChecks()
		self.OutputFile.unlock()
		self.CurrentChoices = list( self.choices.GetCheckedItems() ) # Currently selected checkboxes
		self._SetIndex()
		self.Layout()
	def __init__(self, parent, OutputFiles, TagsTracker):
		TagChoiceQuestion.__init__(self, parent)

		self.parent = parent
		self.CurrentSource = CicularCounter( len(OutputFiles) ) # Current index in output files, for the source items
		self.OutputFiles = OutputFiles # Array of all output files
		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = OutputFiles[self.CurrentSource.get()] # File data object
		self.TagNames = [] # Names of tags corresponding to each selection name
		self.ChoiceNames = self.TagNames # Names of each selection
		self.choices = None
		self.CurrentChoices = [] # Currently selected checkboxes
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.ButtonSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.LeftSource = wx.Button(self, label = '<', style=wx.BU_EXACTFIT)
		self.IndexEntry = wx.TextCtrl(self, style= wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Editable display for current image index
		self.IndexLabel = wx.StaticText(self, style= wx.ALIGN_CENTER) # Static part of image index display
		self.RightSource = wx.Button(self, label = '>', style=wx.BU_EXACTFIT)
		self.commit = wx.Button(self, label = 'Copy >')

		self.LeftSourceTip = wx.ToolTip('Previous Image')
		self.IndexEntryTip = wx.ToolTip('Source image entry')
		self.IndexLabelTip = wx.ToolTip('Total number of images')
		self.RightSourceTip = wx.ToolTip('Next Image')
		self.CommitTip = wx.ToolTip('Copy Selected Tags')

		self.LeftSource.SetToolTip(self.LeftSourceTip)
		self.IndexEntry.SetToolTip(self.IndexEntryTip)
		self.IndexLabel.SetToolTip(self.IndexLabelTip)
		self.RightSource.SetToolTip(self.RightSourceTip)
		self.commit.SetToolTip(self.CommitTip)

		self.ButtonSizer.AddStretchSpacer(10)
		self.ButtonSizer.Add(self.LeftSource, 0, wx.ALIGN_CENTER_VERTICAL)
		self.ButtonSizer.AddStretchSpacer(1)
		self.ButtonSizer.Add(self.IndexEntry, 0, wx.ALIGN_CENTER)
		self.ButtonSizer.AddStretchSpacer(1)
		self.ButtonSizer.Add(self.IndexLabel, 0, wx.ALIGN_CENTER)
		self.ButtonSizer.AddStretchSpacer(1)
		self.ButtonSizer.Add(self.RightSource, 0, wx.ALIGN_CENTER_VERTICAL)
		self.ButtonSizer.AddStretchSpacer(1)
		self.ButtonSizer.Add(self.commit, 0, wx.ALIGN_CENTER_VERTICAL)
		self.ButtonSizer.AddStretchSpacer(10)
		self.sizer.Add(self.ButtonSizer, 0, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_TOP | wx.TOP | wx.EXPAND)
		self.sizer.AddStretchSpacer(3)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnLeft, id=self.LeftSource.GetId() )
		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRight, id=self.RightSource.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnCommit, id=self.commit.GetId() )

class SessionTagsImporter(wx.SplitterWindow):
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.SourceTags.load(OutputFile)
		self.OwnTags.load(OutputFile)
	def clear(self):
		"Clear the question for the given case."
		self.SourceTags.clear()
		self.OwnTags.clear()
	def disp(self):
		"Display the updated question for the given case."
		self.SourceTags.disp()
		self.OwnTags.disp()
		self.OwnTags.Layout()
	def __init__(self, parent, OutputFiles, TagsTracker):
		wx.SplitterWindow.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.SourceTags = ImageTagsList(self, OutputFiles, TagsTracker)
		self.OwnTags = SessionTags(self, TagsTracker)

		self.SetMinimumPaneSize(1)
		self.SplitVertically(self.SourceTags, self.OwnTags) # FIXME: For some reason, this does not want to split in the center, by default.

class SingleStringEntry(wx.Panel): # This class should never be used on its own
	def _GetValueTemplate(self, get):
		"Template to reduce code duplication in the _GetValue functions of child classes."
		self.OutputFile.lock()
		value = get()
		self.OutputFile.unlock()
		if value is None:
			return ""
		else:
			return value
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
	def _OnRomanize(self, e):
		"Replace Kana characters of selected parts of the string with their Romaji equivalents, using kanji_to_romaj, and update the tags accordingly."
		# XXX: Use this pattern in multiline controls, with great caution.
		indices = list( self.entry.GetSelection() )
		text = self.entry.GetValue()
		if indices[0] == indices[1]:
			indices[0] = 0
			indices[1] = len(text)
		self.entry.ChangeValue( ''.join( (
										   text[ 0:indices[0] ],
										   kanji_to_romaji(text[ indices[0]:indices[1] ]),
										   text[indices[1]:]
										 )
									   )
							  )
		self._SetValue()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile # File data object
	def clear(self):
		"Clear the question for the given case."
		pass
	def disp(self):
		"Display the updated check question for the given case."
		self.entry.ChangeValue( self._GetValue() )
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class NameQuestion(SingleStringEntry):
	def _GetValue(self):
		"Get original value for the name field."
		return self._GetValueTemplate(self.OutputFile.GetName)
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
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.checkbox = wx.CheckBox(self, label= 'Use this name')
		self.EntrySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)

		self.EntrySizer.Add(self.checkbox, 0, wx.ALIGN_CENTER)
		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)

		self.MainSizer.Add(self.EntrySizer, 40, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(15)
		self.MainSizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.MainSizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnChange, id=self.entry.GetId() )
		self.Bind( wx.EVT_CHECKBOX, self._OnChange, id=self.checkbox.GetId() )

class SourceQuestion(SingleStringEntry):
	def _GetValue(self):
		"Get original value for the name field."
		return self._GetValueTemplate(self.OutputFile.GetSource)
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
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.checkbox = wx.CheckBox(self, label= 'Use this source')
		self.EntrySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)

		self.EntrySizer.Add(self.checkbox, 0, wx.ALIGN_CENTER)
		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)

		self.MainSizer.Add(self.EntrySizer, 40, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(15)
		self.MainSizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.MainSizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
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
		pass
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
		return self.QuestionWidgets[self.positions[self.pos.get()].get()]
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
			w.load(self.OutputFiles.ControlFiles[self.pos.get()])
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the message, if possible."
		# TODO: Streamline this to avoid a comparison that happens in the CircularCounter
		if 0 <= message < self.pos.GetMax():
			self._hide()
			self.pos.set(message)
			self._LoadAll()
			self._disp()
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the message, if possible."
		# TODO: Streamline this to avoid a comparison that happens in the CircularCounter
		if 0 <= message < self.positions[self.pos.get()].GetMax():
			self._hide()
			self.positions[self.pos.get()].set(message)
			self._disp()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._hide()
		self.pos.dec()
		self._LoadAll()
		self._disp()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._hide()
		self.pos.inc()
		self._LoadAll()
		self._disp()
	def _OnLeftQuestion(self, message, arg2=None):
		"Shift to the left (-1) question to the current position in the questions array if the position is greater than 0. Otherwise, loop around to the last item."
		self._hide()
		self.positions[self.pos.get()].dec()
		self._disp()
	def _OnRightQuestion(self, message, arg2=None):
		"Shift to the right (+1) question to the current position in the questions array if the position is less than the length of the questions array. Otherwise, loop around to the first item."
		self._hide()
		self.positions[self.pos.get()].inc()
		self._disp()
	def _OnFocusQuestionBody(self, message, arg2=None):
		self._CurrentWidget().SetFocus()
	def __init__(self, parent, TagsTracker, questions, OutputFiles):
		wx.Panel.__init__(self, parent=parent)

		self.NumQuestions = len(questions)
		self.pos = CircularCounter( len(OutputFiles.InputPaths) ) # The position in positions
		self.positions = [CircularCounter(self.NumQuestions) for i in OutputFiles.InputPaths] # The position in questions corresponding to each image

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.OutputFiles = OutputFiles # A FileManager object
		self.QuestionWidgets = [] # wxWidgets corresponding to each question
		for q in questions:
			proportion = 100
			if q.type == OptionQuestionType.RADIO_QUESTION:
				self.QuestionWidgets.append( RadioQuestion(self, TagsTracker, q) )
			elif q.type == OptionQuestionType.CHECK_QUESTION:
				self.QuestionWidgets.append( CheckQuestion(self, TagsTracker, q) )
			elif q.type == QuestionType.ENTRY_QUESTION:
				self.QuestionWidgets.append( EntryQuestion(self, len(OutputFiles.InputPaths), TagsTracker) )
			elif q.type == QuestionType.SESSION_TAGS:
				self.QuestionWidgets.append( SessionTags(self, TagsTracker) )
			elif q.type == QuestionType.NAME_QUESTION:
				self.QuestionWidgets.append( NameQuestion(self) )
				proportion = 0
			elif q.type == QuestionType.SOURCE_QUESTION:
				self.QuestionWidgets.append( SourceQuestion(self) )
				proportion = 0
			elif q.type == QuestionType.SAFETY_QUESTION:
				self.QuestionWidgets.append( SafetyQuestion(self) )
			elif q.type == QuestionType.IMAGE_TAGS_ENTRY:
				self.QuestionWidgets.append( ImageTagsEntry(self, TagsTracker) )
			else: # q.type == QuestionType.SESSION_TAGS_IMPORTER
				self.QuestionWidgets.append( SessionTagsImporter(self, OutputFiles.ControlFiles, TagsTracker) )
			self.sizer.Add(self.QuestionWidgets[-1], proportion, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
			self.QuestionWidgets[-1].Hide()

		self.sizer.AddStretchSpacer(1)
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
