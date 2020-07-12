"Stub classes which constitute common parts of the main question classes."

import re
from sys import platform

import wx

from kanji_to_romaji import kanji_to_romaji

from booruwizard.ui.common import CircularCounter, PathEntry

RE_NOT_WHITESPACE = re.compile(r'\S+')
RE_WHITESPACE = re.compile(r'\s')

class TagChoiceQuestion(wx.Panel): # This class should never be used on its own
	def SetChoicesTip(self):
		if self.ChoicesTipText is not None:
			self.choices.SetToolTip( wx.ToolTip(self.ChoicesTipText) )
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
		self.OutputFile.lock()
		for i, n in enumerate(self.TagNames):
			self._UpdateName(i)
			occurrences = self.OutputFile.tags.ReturnStringOccurrences(n)
			if n and occurrences > 0:
				if occurrences == 2:
					self.CurrentChoices.append(i)
				self.choices.Check(i)
			else:
				self.choices.Check(i, False)
		self.OutputFile.unlock()
	def _OnSelect(self, e):
		"Bound to EVT_CHECKLISTBOX; set selected tags and remove the previously selected ones."
		self._UpdateChoice( e.GetInt() )
		self._UpdateChecks()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.OutputFile = OutputFile
	def clear(self):
		"Clear the question for the given case."
		pass
	def disp(self):
		"Display the updated check question for the given case."
		self._UpdateChecks()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class ArbitraryCheckQuestion(TagChoiceQuestion):  # This class should never be used on its own
	def SetChoices(self, names):
		self.TagNames = names
		self.ChoiceNames = self.TagNames # Names of each selection
		if self.choices is not None:
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.sizer.Remove(0)
			self.choices.Destroy()
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
		self.SetChoicesTip()
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.sizer.Layout()
		if self.OutputFile is not None:
			self._UpdateChecks()
	def __init__(self, parent, TagsTracker):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.ChoicesTipText = None
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self.sizer)
		self.choices = None
		self.SetChoices([])
		self.CurrentChoices = [] # Currently selected checkboxes

class EntryBase(wx.Panel):  # This class should never be used on its own
	def load(self, OutputFile):
		"Initialize the entry question for a certain case."
		self.OutputFile = OutputFile
	def _UpdateTags(self):
		pass
	def clear(self):
		"Clear the entry question for the given case."
		self._UpdateTags()
	def SetRomanizeButtonState(self):
		if self.entry.GetValue():
			self.RomanizeButton.Enable()
		else:
			self.RomanizeButton.Disable()
	def _OnUpdateEvent(self, e):
		"Generic event handler, to update tags based on the contents of the field."
		self._UpdateTags()
		self.SetRomanizeButtonState()
		e.Skip()
	def _DoRomanize(self):
		"Replace Kana characters of selected parts of the string with their Romaji equivalents, using kanji_to_romaj."
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
		return ''.join(OutputStrings)
	def _OnRomanize(self, e):
		"Replace Kana characters of selected parts of the string with their Romaji equivalents, using kanji_to_romaj, and update the tags accordingly."
		self.entry.ChangeValue( self._DoRomanize() )
		self._UpdateTags()
		e.Skip()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

class StoragelessEntry(EntryBase):
	def load(self, OutputFile):
		pass
	def disp(self):
		self.SetRomanizeButtonState()
	def _OnRomanize(self, e):
		"Replace Kana characters of selected parts of the string with their Romaji equivalents, using kanji_to_romaj, and update the tags accordingly."
		self.entry.SetValue( self._DoRomanize() )
		e.Skip()
	def __init__(self, parent):
		EntryBase.__init__(self, parent=parent)

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

class SplitterBase(wx.SplitterWindow): # This class should never be used on its own
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		self.first.load(OutputFile)
		self.second.load(OutputFile)
	def clear(self):
		"Clear the question for the given case."
		self.first.clear()
		self.second.clear()
	def disp(self):
		"Display the updated question for the given case."
		self.first.disp()
		self.second.disp()
		self.second.Layout()

class ImageTagsList(TagChoiceQuestion): # This class should never be used on its own
	def _SetIndex(self):
		self.IndexEntry.SetValue( str(self.CurrentSource.get() + 1) )
		self.IndexLabel.SetLabel( ''.join( ( ' /', str(self.CurrentSource.GetMax() + 1) ) ) )
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
		try:
			value = int( self.IndexEntry.GetValue() ) - 1
			success = self.CurrentSource.set(value)
		except ValueError:
			success = False
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
	def _OnPathSearch(self, e):
		"Update the search menu, based on matches found in the paths array."
		self.PathEntry.UpdateMenu()
		e.Skip()
	def _OnPathEntry(self, e):
		"Send an IndexImage message, if the index of PathEntry contents can be found in paths; otherwise, try to autocomplete the contents."
		try:
			value = self.PathEntry.SearchPath( self.PathEntry.GetPath() )
			self.CurrentSource.set(value)
			self.OutputFile = self.OutputFiles[value]
			self.disp()
		except ValueError: # TODO: Should this work with any exception?
			self.PathEntry.UpdateAutocomplete()
		e.Skip()
	def _OnMenuPathChosen(self, e):
		"Set the path entry to the chosen menu value."
		self.PathEntry.ChooseMenuItem(e.GetId())
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		pass
	def disp(self):
		"Display the updated question for the given case."
		self.PathEntry.SetPath( self.CurrentSource.get() )
		if self.choices is not None:
			self.Unbind( wx.EVT_CHECKLISTBOX, id=self.choices.GetId() )
			self.sizer.Remove(5)
			self.choices.Destroy()
			self.choices = None
		self.ChoiceNames = self._MakeNames()
		self.TagNames = self.ChoiceNames
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
		self.SetChoicesTip()
		self.sizer.Add(self.choices, 100, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self._UpdateChecks()
		self.CurrentChoices = list( self.choices.GetCheckedItems() ) # Currently selected checkboxes
		self._SetIndex()
		self.Layout()
	def __init__(self, parent, OutputFiles, TagsTracker):
		TagChoiceQuestion.__init__(self, parent)

		self.parent = parent
		self.CurrentSource = CircularCounter(len(OutputFiles) - 1) # Current index in output files, for the source items
		self.OutputFiles = OutputFiles # Array of all output files
		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = OutputFiles[self.CurrentSource.get()] # File data object
		self.TagNames = [] # Names of tags corresponding to each selection name
		self.ChoiceNames = self.TagNames # Names of each selection
		self.choices = None
		self.CurrentChoices = [] # Currently selected checkboxes
		self.PathEntry = PathEntry( self, tuple( (f.FullPath for f in self.OutputFiles) ) )
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
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.ButtonSizer, 0, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_TOP | wx.TOP | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.PathEntry.entry, 0, wx.CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.SetSizer(self.sizer)

		for i in self.PathEntry.GetMenuItemIds():
			self.Bind(wx.EVT_MENU, self._OnMenuPathChosen, id=i)

		if len(OutputFiles) <= 1:
			self.LeftSource.Disable()
			self.RightSource.Disable()

		self.Bind( wx.EVT_BUTTON, self._OnLeft, id=self.LeftSource.GetId() )
		self.Bind( wx.EVT_TEXT_ENTER, self._OnIndexEntry, id=self.IndexEntry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRight, id=self.RightSource.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnCommit, id=self.commit.GetId() )
		self.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self._OnPathSearch, id=self.PathEntry.entry.GetId() )
		self.Bind( wx.EVT_TEXT_ENTER, self._OnPathEntry, id=self.PathEntry.entry.GetId() )

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
		return self._GetValueTemplate(self._ValueGetter)
	def _SetValue(self): # This determines where the field puts its value; define it in child classes
		"Set value controlled by this field."
		value = self.entry.GetValue()
		self.OutputFile.PrepareChange()
		self._ValueSetter(value)
		self.OutputFile.FinishChange()
	def SetRomanizeButtonState(self):
		if self.entry.GetValue():
			self.RomanizeButton.Enable()
		else:
			self.RomanizeButton.Disable()
	def _OnChange(self, e):
		"Set the value."
		self._SetValue()
		self.SetRomanizeButtonState()
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
		self.SetRomanizeButtonState()
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
