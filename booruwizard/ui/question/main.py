"The components associated with the question (third from the top) GUI frame."

import re

from urllib.request import urlopen
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError

from saucenao_api import SauceNao
from saucenao_api.errors import UnknownApiError, UnknownServerError, UnknownClientError, BadKeyError, BadFileSizeError, ShortLimitReachedError, LongLimitReachedError, SauceNaoApiError

import wx
import wx.lib.scrolledpanel
from pubsub import pub

from booruwizard.lib.fileops import safety
from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import QuestionType, OptionQuestionType
from booruwizard.lib.netcode import HeadRequest
from booruwizard.ui.common import CircularCounter, PathEntry, RenderThreeIfMid
from booruwizard.ui.question.base import RE_NOT_WHITESPACE, TagChoiceQuestion, ArbitraryCheckQuestion, EntryBase, PathNumberChooser, StoragelessEntry, SplitterBase, SimilarTagsFinder, ImageTagsList, SingleStringEntry, ToggleCopyArbitraryCheckQuestion

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
		self.ChoicesTip = wx.ToolTip("Select a tag here. Empty options set no tag.")
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.choices.SetToolTip(self.ChoicesTip)

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_RADIOBOX, self._OnSelect, id=self.choices.GetId() )

		self.SetOwnBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) )
		self.SetupScrolling()

class CheckQuestion(TagChoiceQuestion):
	def __init__(self, parent, TagsTracker, PanelQuestion):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = PanelQuestion.GetChoiceTags() # Names of tags corresponding to each selection name
		self.ChoiceNames = PanelQuestion.GetChoiceNames() # Names of each selection
		self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
		self.ChoicesTipText = "Select tags to be written, here."
		self.CurrentChoices = [] # Currently selected checkboxes
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.SetChoicesTip()

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )

class CustomTags(SplitterBase):
	def _OnEntryChange(self, e):
		self.second.SetChoices( self.first.entry.GetValue().split() )
		self.first.SetRomanizeButtonState() # TODO: Handle this in a callback local to the class?
		e.Skip()
	def __init__(self, parent, DefaultTags, TagsTracker):
		SplitterBase.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.first = StoragelessEntry(self)
		self.second = ArbitraryCheckQuestion(self, TagsTracker)

		self.EntryTip = wx.ToolTip("Enter tags here. They will be displayed to the right.")
		self.first.entry.SetToolTip(self.EntryTip)
		self.second.ChoicesTipText = "Select tags to be written to file, here."
		self.second.SetChoicesTip()

		self.SetMinimumPaneSize( self.GetSize().GetWidth() )
		self.SplitVertically(self.first, self.second)

		self.Bind( wx.EVT_TEXT, self._OnEntryChange, id=self.first.entry.GetId() )

		self.first.entry.SetValue(DefaultTags)

class EntryQuestion(EntryBase):
	def _UpdateEntryText(self):
		"Update the current entry text according to which tags can actually be found in the output file."
		self.CurrentTags = TagsContainer()
		OldStrings = []
		OldTags = []
		SpaceStart = 0
		while True:
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
		self.SetRomanizeButtonState()
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
		self.pos = CircularCounter(NumImages - 1) # Position in entry strings
		self.EntryStrings = [""] * NumImages # The contents of the entry boxes must be saved between images.
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)
		self.EntryTip = wx.ToolTip("Enter tags to be written, here.")
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.entry.SetToolTip(self.EntryTip)
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
		self.SetRomanizeButtonState()
	def __init__(self, parent, TagsTracker):
		EntryBase.__init__(self, parent=parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)
		self.EntryTip = wx.ToolTip("All tags present in the image are displayed here, and can be edited freely.")
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.CurrentString = []

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)
		self.entry.SetToolTip(self.EntryTip)

		self.sizer.Add(self.entry, 55, wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnUpdateEvent, id=self.entry.GetId() )
		self.Bind( wx.EVT_WINDOW_DESTROY, self._OnUpdateEvent, id=self.GetId() ) # TODO Should we bind to EVT_SET_FOCUS too?

class SessionTags(TagChoiceQuestion):
	def _MakeNamesFrom(self, func):
		RawNames = func()
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
	def _MakeNames(self):
		return self._MakeNamesFrom(self.TagsTracker.ReturnStringList)
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
			self.choices = wx.CheckListBox(self, choices= self.ChoiceNames)
			self.SetChoicesTip()
			self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
			self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
			self.Bind( wx.EVT_SCROLL_TOP, self._OnScrollTop, id=self.choices.GetId() )
			self.sizer.Layout()
		self._UpdateChecks()
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
		self.SetChoicesTip()
		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_CHECKLISTBOX, self._OnSelect, id=self.choices.GetId() )
		self.Bind( wx.EVT_SCROLL_TOP, self._OnScrollTop, id=self.choices.GetId() )
		self._UpdateChecks()
	def __init__(self, parent, TagsTracker):
		TagChoiceQuestion.__init__(self, parent)

		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFile = None # File data object
		self.TagNames = [] # Names of tags corresponding to each selection name
		self.ChoiceNames = self.TagNames # Names of each selection
		self.choices = None
		self.ChoicesTipText = "All tags in use are displayed here, and can be edited freely."
		self.CurrentChoices = [] # Currently selected checkboxes
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.SetSizer(self.sizer)

class AddedTags(SessionTags):
	def _FilterStringList(self):
		output = []
		self.OutputFile.lock()
		for n in self.TagsTracker.ReturnStringList():
			if not self.TagsTracker.HasConfigTag(n):
				output.append(n)
		self.OutputFile.unlock()
		return output
	def _MakeNames(self):
		return self._MakeNamesFrom(self._FilterStringList)
	def __init__(self, parent, TagsTracker):
		SessionTags.__init__(self, parent, TagsTracker)
		self.ChoicesTipText = "All tags in use and not automatically set by the software are displayed here, and can be edited freely."

class AddedTagsEntry(SplitterBase):
	def _OnEntryQuestionChange(self, e):
		self.second.disp()
		self.second.Layout()
		e.Skip()
	def __init__(self, parent, NumImages, OutputFiles, TagsTracker):
		wx.SplitterWindow.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.first = EntryQuestion(self, NumImages, TagsTracker)
		self.second = AddedTags(self, TagsTracker)

		self.SetMinimumPaneSize( self.GetSize().GetWidth() )
		self.SplitVertically(self.first, self.second)

		self.Bind( wx.EVT_BUTTON, self._OnEntryQuestionChange, id=self.first.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnEntryQuestionChange, id=self.first.entry.GetId() )

class NativeTags(AddedTags):
	def _FilterStringList(self):
		self.OutputFile.lock()
		output = self.TagsTracker.ReturnConfigTagList()
		self.OutputFile.unlock()
		return output

class SessionTagsImporter(SplitterBase):
	def __init__(self, parent, OutputFiles, TagsTracker):
		wx.SplitterWindow.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.first = ImageTagsList(self, OutputFiles, TagsTracker)
		self.first.ChoicesTipText = "Select tags to copy over. Only those not already present in the current image will be listed."
		self.second = SessionTags(self, TagsTracker)
		self.OwnTags = self.second

		self.SetMinimumPaneSize( self.GetSize().GetWidth() )
		self.SplitVertically(self.first, self.second)

class BulkTagger(wx.Panel):
	def clear(self):
		pass
	def load(self, OutputFile):
		pass
	def _SetSwapEntryButtonState(self):
		if self.RemoveEntry.GetValue() or self.AddEntry.GetValue():
			self.SwapEntryButton.Enable()
		else:
			self.SwapEntryButton.Disable()
	def disp(self):
		self._SetSwapEntryButtonState()
	def _SetActionButtons(self, EnableRemove, EnableReplace, EnableAlias, EnableAdd):
		self.RemoveButton.Enable(EnableRemove)
		self.ReplaceButton.Enable(EnableReplace)
		self.AliasButton.Enable(EnableAlias)
		self.AddButton.Enable(EnableAdd)
	def _DisableButtons(self):
		self._SetActionButtons(False, False, False, False)
	def _CalculateTagCoverage(self):
		"Compute the valid actions based on which tags are selected for which indices."
		RemoveTags = tuple( ( e.strip() for e in self.RemoveEntry.GetValue().split() ) )
		AddTags = tuple( ( e.strip() for e in self.AddEntry.GetValue().split() ) )
		EnableRemove = False
		EnableReplace = False
		EnableAlias = False
		EnableAdd = False
		for i in self.NumberChooser.indices:
			f = self.OutputFiles[i]
			CurrentHasRemove = False
			CurrentHasAdd = False
			f.lock()
			if f.tags.HasAnyOfStringList(RemoveTags):
				EnableRemove = True
				CurrentHasRemove = True
			if not f.tags.HasAllOfStringList(AddTags):
				EnableAdd = True
				CurrentHasAdd = True
			f.unlock()
			if CurrentHasRemove and CurrentHasAdd:
				EnableAlias = True
				EnableReplace = True
				break
		self._SetActionButtons(EnableRemove, EnableReplace, EnableAlias, EnableAdd)
	def _OnNumberEntry(self, e):
		if self.NumberChooser.ProcessNumbers():
			self._CalculateTagCoverage()
		else:
			self._DisableButtons()
		e.Skip()
	def _OnUpdate(self, e):
		self._CalculateTagCoverage()
		self._SetSwapEntryButtonState()
		e.Skip()
	def _OnSwapEntryButton(self, e):
		tmp = self.RemoveEntry.GetValue()
		self.RemoveEntry.SetValue( self.AddEntry.GetValue() )
		self.AddEntry.SetValue(tmp)
		e.Skip()
	def _OnRemoveButton(self, e):
		RemoveTags = tuple( en.strip() for en in self.RemoveEntry.GetValue().split() )
		for i in self.indices:
			f = self.OutputFiles[i]
			f.PrepareChange()
			self.TagsTracker.SubStringList(f.tags.ReturnStringList(), 1)
			f.tags.ClearStringList(RemoveTags, 2)
			self.TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)
			f.FinishChange()
		self._CalculateTagCoverage()
		e.Skip()
	def _OnReplaceButton(self, e):
		RemoveTags = tuple( en.strip() for en in self.RemoveEntry.GetValue().split() )
		AddTags = tuple( en.strip() for en in self.AddEntry.GetValue().split() )
		for i in self.NumberChooser.indices:
			f = self.OutputFiles[i]
			f.PrepareChange()
			if f.tags.HasAnyOfStringList(RemoveTags):
				self.TagsTracker.SubStringList(f.tags.ReturnStringList(), 1)
				f.tags.ClearStringList(RemoveTags, 2)
				f.tags.SetStringList(AddTags, 2)
				self.TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)
			f.FinishChange()
		self._CalculateTagCoverage()
		e.Skip()
	def _OnAliasButton(self, e):
		RemoveTags = tuple( en.strip() for en in self.RemoveEntry.GetValue().split() )
		AddTags = tuple( en.strip() for en in self.AddEntry.GetValue().split() )
		for i in self.NumberChooser.indices:
			f = self.OutputFiles[i]
			f.PrepareChange()
			if f.tags.HasAnyOfStringList(RemoveTags):
				self.TagsTracker.SubStringList(f.tags.ReturnStringList(), 1)
				f.tags.SetStringList(AddTags, 2)
				self.TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)
			f.FinishChange()
		self._CalculateTagCoverage()
		e.Skip()
	def _OnAddButton(self, e):
		AddTags = tuple( en.strip() for en in self.AddEntry.GetValue().split() )
		for i in self.NumberChooser.indices:
			f = self.OutputFiles[i]
			f.PrepareChange()
			self.TagsTracker.SubStringList(f.tags.ReturnStringList(), 1)
			f.tags.SetStringList(AddTags, 2)
			self.TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)
			f.FinishChange()
		self._CalculateTagCoverage()
		e.Skip()
	def __init__(self, parent, OutputFiles, TagsTracker):
		wx.Panel.__init__(self, parent=parent)

		# Data
		self.TagsTracker = TagsTracker # Global record of the number of tags in use
		self.OutputFiles = OutputFiles # File data object

		# Index selection controls
		self.NumberChooser = PathNumberChooser(self, OutputFiles)

		# Tag entry controls
		self.RemoveEntry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)
		self.SwapEntryButton = wx.Button(self, label='Swap')
		self.AddEntry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL | wx.TE_MULTILINE)

		# Action controls
		self.RemoveButton = wx.Button(self, label='^ Remove')
		self.ReplaceButton = wx.Button(self, label='> Replace >')
		self.AliasButton = wx.Button(self, label='> Alias >')
		self.AddButton = wx.Button(self, label='Add ^')
		self._DisableButtons()

		# Tooltips
		self.RemoveEntryTip = wx.ToolTip('Tags to be removed.')
		self.SwapEntryButtonTip = wx.ToolTip("Swap the two entries.")
		self.AddEntryTip = wx.ToolTip('Tags to be added.')
		self.RemoveButtonTip = wx.ToolTip('Remove the tags listed in the left (remove) entry.')
		self.ReplaceButtonTip = wx.ToolTip('If any tags listed in the left (remove) entry can be found, do the remove then add actions.')
		self.AliasButtonTip = wx.ToolTip('If any tags listed in the left (remove) entry can be found, do the add action.')
		self.AddButtonTip = wx.ToolTip('Add the tags listed in the right (add) entry.')

		# Setting tooltips
		self.RemoveEntry.SetToolTip(self.RemoveEntryTip)
		self.SwapEntryButton.SetToolTip(self.SwapEntryButtonTip)
		self.AddEntry.SetToolTip(self.AddEntryTip)
		self.RemoveButton.SetToolTip(self.RemoveButtonTip)
		self.ReplaceButton.SetToolTip(self.ReplaceButtonTip)
		self.AliasButton.SetToolTip(self.AliasButtonTip)
		self.AddButton.SetToolTip(self.AddButtonTip)

		# Event binding
		self.NumberChooser.PathEntry.SelfBinds()
		self.NumberChooser.SelfBinds()
		self.Bind( wx.EVT_BUTTON, self._OnSwapEntryButton, id=self.SwapEntryButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnNumberEntry, id=self.NumberChooser.NumberEntry.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnUpdate, id=self.RemoveEntry.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnUpdate, id=self.AddEntry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRemoveButton, id=self.RemoveButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnReplaceButton, id=self.ReplaceButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnAliasButton, id=self.AliasButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnAddButton, id=self.AddButton.GetId() )

		# Sizers
		self.SelectionSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.EntrySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.ConditionalActionSizer = wx.BoxSizer(wx.VERTICAL)
		self.ActionSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		# Layout
		self.SelectionSizer.Add(self.NumberChooser.PathEntryLabel, 0, wx.CENTER | wx.ALIGN_CENTER)
		self.SelectionSizer.AddStretchSpacer(1)
		self.SelectionSizer.Add(self.NumberChooser.PathEntry.entry, 50, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.SelectionSizer.AddStretchSpacer(1)
		self.SelectionSizer.Add(self.NumberChooser.NumberEntryLabel, 0, wx.CENTER | wx.ALIGN_CENTER)
		self.SelectionSizer.AddStretchSpacer(1)
		self.SelectionSizer.Add(self.NumberChooser.NumberEntry, 50, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)

		self.EntrySizer.Add(self.RemoveEntry, 75, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.SwapEntryButton, 0, wx.CENTER | wx.ALIGN_CENTER | wx.SHAPED)
		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.AddEntry, 75, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)

		self.ConditionalActionSizer.Add(self.ReplaceButton, 0, wx.CENTER | wx.ALIGN_CENTER | wx.SHAPED)
		self.ConditionalActionSizer.AddStretchSpacer(1)
		self.ConditionalActionSizer.Add(self.AliasButton, 0, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)

		self.ActionSizer.AddStretchSpacer(100)
		self.ActionSizer.Add(self.RemoveButton, 0, wx.CENTER | wx.ALIGN_CENTER | wx.SHAPED)
		self.ActionSizer.AddStretchSpacer(5)
		self.ActionSizer.Add(self.ConditionalActionSizer, 0, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.ActionSizer.AddStretchSpacer(5)
		self.ActionSizer.Add(self.AddButton, 0, wx.CENTER | wx.ALIGN_CENTER | wx.SHAPED)
		self.ActionSizer.AddStretchSpacer(100)

		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.SelectionSizer, 4, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.EntrySizer, 50, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)
		self.sizer.Add(self.ActionSizer, 18, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(2)

		self.SetSizer(self.sizer)

class NameQuestion(SingleStringEntry):
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile
		self._ValueGetter = self.OutputFile.GetName
		self._ValueSetter = self.OutputFile.SetName
	def __init__(self, parent, TagsTracker):
		SingleStringEntry.__init__(self, parent)

		self.OutputFile = None # File data object
		self._ValueSetter = None
		self._ValueGetter = None
		self.TagsTracker = TagsTracker
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.EntryTip = wx.ToolTip("Set name to use here.")
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.EntrySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)

		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)
		self.entry.SetToolTip(self.EntryTip)

		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)

		self.MainSizer.Add(self.EntrySizer, 40, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(15)
		self.MainSizer.Add(self.RomanizeButton, 0, wx.ALIGN_LEFT | wx.LEFT | wx.SHAPED)
		self.SetSizer(self.MainSizer)

		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnChange, id=self.entry.GetId() )

class SourceQuestion(SingleStringEntry):
	def _SetPathFormatReplacement(self):
		self.PathFormatReplacement = None
		self.OutputFile.lock()
		FullPath = self.OutputFile.FullPath
		self.OutputFile.unlock()
		PatternValue = self.PathFormatPatternEntry.GetValue()
		ReplaceValue = self.PathFormatReplaceEntry.GetValue()
		if PatternValue and ReplaceValue:
			try:
				PotentialReplacement = None
				if re.search(PatternValue, FullPath) is not None:
					PotentialReplacement = re.sub(PatternValue,
												  ReplaceValue,
												  FullPath)
				if PotentialReplacement != self.entry.GetValue():
					self.PathFormatReplacement = PotentialReplacement
			except (re.error, IndexError):
				pass
	def _SetSourceTestButtonState(self):
		uri = urlparse( self.entry.GetValue() )
		if uri.scheme != 'http' and uri.scheme != 'https':
			self.BadIdChoicesLabel.SetLabel("Source URI scheme must be 'http' or 'https'.")
			self.SourceTestButton.Disable()
		elif not uri.netloc:
			self.BadIdChoicesLabel.SetLabel("Source URI does not specify a domain.")
			self.SourceTestButton.Disable()
		elif not uri.path:
			self.BadIdChoicesLabel.SetLabel("Source URI does not specify a path.")
			self.SourceTestButton.Disable()
		else:
			self.BadIdChoicesLabel.SetLabel("Source URI ready for testing.")
			self.SourceTestButton.Enable()
		self.BadIdChoicesContainerSizer.Layout()
	def _SetSourceSearchButtonState(self):
		# TODO: Prevent further searches if results for an image are already loaded?
		if self.images.get( self.pos.get() ).image is not None:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Ready to search for loaded image.", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
			self.SourceSearchButton.Enable()
		else:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Failed to load image for searching.", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
			self.SourceSearchButton.Disable()
		self.SourceChoicesContainerSizer.Layout()
	def _SetPathFormatButtonState(self):
		if self.PathFormatReplacement is not None:
			self.PathFormatButton.Enable()
		else:
			self.PathFormatButton.Disable()
	def _SetBulkSourceButtonState(self):
		EntryValue = self.entry.GetValue()
		state = False
		if self.NumberChooser.indices and EntryValue:
			done = False
			for i in self.NumberChooser.indices:
				f = self.OutputFiles[i]
				f.lock()
				if f.GetSource() != EntryValue:
					state = True
					done = True
				f.unlock()
				if done:
					break
		self.BulkSourceButton.Enable(state)
	def SetButtonStates(self):
		#TODO Rewrite?
		self.SetRomanizeButtonState()
		self._SetSourceTestButtonState()
		self._SetSourceSearchButtonState()
		self._SetPathFormatButtonState()
		self._SetBulkSourceButtonState()
	def _MenuItemExists(self, value, menu):
		for i in menu.GetMenuItems():
			if value == i.GetItemLabel():
				return True
		return False
	def _AddPathFormatMenuItem(self, value, menu, func):
		if not self._MenuItemExists(value, menu):
			NewId = wx.NewId()
			item = wx.MenuItem(menu, NewId, value, value)
			menu.Append(item)
			self.Bind(wx.EVT_MENU, func, id=NewId)
	def _UpdatePathFormatMenuItems(self):
		self._AddPathFormatMenuItem(self.PathFormatPatternEntry.GetValue(), self.PathFormatPatternMenu, self._OnPathFormatPatternMenuItemChosen)
		self._AddPathFormatMenuItem(self.PathFormatReplaceEntry.GetValue(), self.PathFormatReplaceMenu, self._OnPathFormatReplaceMenuItemChosen)
	def load(self, OutputFile):
		"Initialize the check question for a certain case."
		self.OutputFile = OutputFile
		self._ValueGetter = self.OutputFile.GetSource
		self._ValueSetter = self.OutputFile.SetSource
		self.BadIdChoices.load(OutputFile)
	def clear(self):
		"Clear the question for the given case."
		self.BadIdChoices.clear()
	def _SetSourceChoicesTip(self):
		if self.SourceChoicesTipText is not None:
			self.SourceChoices.UnsetToolTip()
			self.SourceChoices.SetToolTip( wx.ToolTip(self.SourceChoicesTipText) )
	def _UpdateSourceChoicesSelection(self):
		SelectionIndex = 0
		try:
			results = self.SourceChoicesResults[self.pos.get()]
			if results:
				SelectionIndex = results.index( self.entry.GetValue() )
		except ValueError:
			pass
		self.SourceChoices.SetSelection(SelectionIndex)
	def _UpdateSourceChoices(self):
		CurrentResults = self.SourceChoicesResultsNames[self.pos.get()]
		if not CurrentResults:
			CurrentResults = ['<CUSTOM>']
		else:
			CurrentResults = [r.replace('&', '') for r in CurrentResults]  #XXX: Remove GTK 'mnemonic' characters.
		self.Unbind( wx.EVT_RADIOBOX, id=self.SourceChoices.GetId() )
		self.SourceChoicesSizer.Remove(0)
		self.SourceChoices.Destroy()
		self.SourceChoices = wx.RadioBox(self.SourceChoicesScrollable, choices=CurrentResults, style= wx.RA_SPECIFY_ROWS | wx.BORDER_NONE)
		self._SetSourceChoicesTip()
		self.SourceChoicesSizer.Add(self.SourceChoices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.Bind( wx.EVT_RADIOBOX, self._OnSourceChoices, id=self.SourceChoices.GetId() )
		self.MainSizer.Layout()
		self._UpdateSourceChoicesSelection()
	def disp(self):
		"Display the updated check question for the given case."
		super().disp()
		self._UpdateSourceChoices()
		self.BadIdChoices.disp()
		self._SetPathFormatReplacement()
		self.SetButtonStates()
	def _UpdateChange(self):
		self._SetValue()
		self._SetPathFormatReplacement()
		self.SetButtonStates()
		self._UpdateSourceChoicesSelection()
	def _OnChange(self, e):
		"Set the value."
		self._UpdateChange()
		e.Skip()
	def _OnPathFormatButton(self, e):
		self.entry.ChangeValue(self.PathFormatReplacement)
		self._UpdatePathFormatMenuItems()
		self._UpdateChange()
		e.Skip()
	def _OnPathFormatEntry(self, e):
		self._SetPathFormatReplacement()
		self._SetPathFormatButtonState()
		e.Skip()
	def _OnPathFormatPatternMenuItemChosen(self, e):
		#TODO: Rewrite?
		self.PathFormatPatternEntry.SetValue( self.PathFormatPatternMenu.FindItemById( e.GetId() ).GetItemLabel() )
		#self._SetPathFormatReplacement()
		#self._SetPathFormatButtonState()
		e.Skip()
	def _OnPathFormatReplaceMenuItemChosen(self, e):
		#TODO: Rewrite?
		self.PathFormatReplaceEntry.SetValue( self.PathFormatReplaceMenu.FindItemById( e.GetId() ).GetItemLabel() )
		#self._SetPathFormatReplacement()
		#self._SetPathFormatButtonState()
		e.Skip()
	def _OnSourceTestButton(self, e):
		self.BadIdChoicesLabel.SetLabel("Requesting source URI.")
		try:
			request = HeadRequest( self.entry.GetValue() )
			request.add_header("User-Agent", self.SourceTestUserAgent)
			try:
				response = urlopen(request)
				self.BadIdChoicesLabel.SetLabel( ''.join( ("Successfully opened source URI (", str(response.status), " ", str(response.reason), ")") ) )
			except HTTPError as err:
				self.BadIdChoicesLabel.SetLabel( ''.join( ("Unable to open source URI (", str(err.code), " ", str(err.reason), ")") ) )
			except URLError as err:
				self.BadIdChoicesLabel.SetLabel( ''.join( ("Unable to parse source URI (", str(err.reason), ")") ) )
		except ValueError as err:
			self.BadIdChoicesLabel.SetLabel( ''.join( ("Unrecognized URI format.") ) )
		self.BadIdChoicesContainerSizer.Layout()
		e.Skip()
	def _OnSourceSearchButton(self, e):
		self.SourceChoicesLabel.SetLabel( ''.join( ( "Searching for loaded image.", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		try:
			stream = open(self.images.get( self.pos.get() ).path, 'rb')
			results = SauceNao().from_file(stream)
			stream.close()
			self.SourceChoicesResultsNames[self.pos.get()] = ['<CUSTOM>']
			self.SourceChoicesResults[self.pos.get()] = [None]
			for r in results:
				BaseName = ''.join( (str(r.similarity), '%-', str(r.author), '-', str(r.title)) )
				UrlAdded = False
				for u in r.urls:
					UrlAdded = True
					self.SourceChoicesResultsNames[self.pos.get()].append( ''.join( (BaseName, '-', u) ) )
					self.SourceChoicesResults[self.pos.get()].append( str(u) )
				if not UrlAdded:
					self.SourceChoicesResultsNames[self.pos.get()].append(BaseName)
					self.SourceChoicesResults[self.pos.get()].append( str(r.title) )
			self.SourceChoicesRemainingSearches = str(results.long_remaining)
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Loaded image successfully searched.", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except UnknownServerError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Unknown server)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except UnknownClientError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Unknown client)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except UnknownApiError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Unknown error)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except BadKeyError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Bad key)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except BadFileSizeError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Bad file size)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except ShortLimitReachedError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (SauceNAO burst limit reached)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except LongLimitReachedError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (SauceNAO daily limit reached)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except SauceNaoApiError:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (Generic error)", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		except OSError as err:
			self.SourceChoicesLabel.SetLabel( ''.join( ( "Unable to search for loaded image. (IO error: ", str(err.errno), " ", err.strerror, ")", RenderThreeIfMid(' (Remaining daily searches: ', self.SourceChoicesRemainingSearches, ')') ) ) )
		self._UpdateSourceChoices()
		self.SourceChoicesContainerSizer.Layout()
		e.Skip()
	def _OnSourceChoices(self, e):
		selection = self.SourceChoices.GetSelection()
		if selection > 0:
			OldValue = self.entry.GetValue()
			NewValue = self.SourceChoicesResults[self.pos.get()][selection]
			if OldValue != NewValue:
				self.entry.ChangeValue(NewValue)
				self._SetValue()
				self._SetPathFormatReplacement()
				self.SetRomanizeButtonState()
				self._SetSourceTestButtonState()
				self._SetPathFormatButtonState()
		e.Skip()
	def _OnSourceChoicesContainerSize(self, e):
		self.BadIdChoicesContainer.SetMaxSize( self.SourceChoicesContainer.GetSize() )
		e.Skip()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the message, if possible."
		self.pos.set(message)
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the entry string array if the pos is less than the length of the entry string array. Otherwise, loop around to the first item."
		self.pos.inc()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the entry string array if the pos is greater than 0. Otherwise, loop around to the last item."
		self.pos.dec()
	def _OnNumberEntry(self, e):
		self.NumberChooser.ProcessNumbers()
		self._SetBulkSourceButtonState()
		e.Skip()
	def _OnBulkSourceButton(self, e):
		for i in self.NumberChooser.indices:
			f = self.OutputFiles[i]
			f.PrepareChange()
			f.SetSource( self.entry.GetValue() )
			f.FinishChange()
		self._SetBulkSourceButtonState()
		e.Skip()
	def __init__(self, parent, q, OutputFiles, TagsTracker, images):
		SingleStringEntry.__init__(self, parent)

		self.OutputFiles = OutputFiles
		NumImages = len(OutputFiles)
		self.images = images
		self.OutputFile = None # File data object
		self._ValueSetter = None
		self._ValueGetter = None
		self.TagsTracker = TagsTracker
		self.entry = wx.TextCtrl(self, style= wx.TE_NOHIDESEL)
		self.EntryTip = wx.ToolTip("Enter source here.")
		self.RomanizeButton = wx.Button(self, label='Romanize Kana Characters')
		self.RomanizeButtonTip = wx.ToolTip('Convert selected (or all) Kana characters to their Romaji equivalents.')
		self.DisplaySplitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
		self.pos = CircularCounter(NumImages - 1) # Position in entry strings
		self.SourceChoicesRemainingSearches = None
		self.SourceChoicesResults = [None] * NumImages # The results for SourceSearchButton shall be saved to avoid overusing SauceNao
		self.SourceChoicesResultsNames = [None] * NumImages # The results for SourceSearchButton shall be saved to avoid overusing SauceNao
		self.SourceChoicesContainer = wx.Panel(self.DisplaySplitter)
		self.SourceSearchButton = wx.Button(self.SourceChoicesContainer, label='Search Source Image')
		self.SourceSearchButtonTip = wx.ToolTip('Attempt to search for the image on SauceNao')
		self.SourceChoicesLabel = wx.StaticText(self.SourceChoicesContainer, style= wx.ALIGN_CENTER)
		self.SourceChoicesLabelTip = wx.ToolTip("The status of the search performed by the 'Search Source Image' button.")
		self.SourceChoicesScrollable = wx.lib.scrolledpanel.ScrolledPanel(self.SourceChoicesContainer)
		#TODO: Wrap up first version of this into the same function used when the choices are updated?
		self.SourceChoices = wx.RadioBox(self.SourceChoicesScrollable, choices=['<CUSTOM>'], style= wx.RA_SPECIFY_ROWS | wx.BORDER_NONE)
		self.SourceChoicesTipText = "Usable results of 'Search Source Image' are displayed here."
		self.BadIdChoicesContainer = wx.Panel(self.DisplaySplitter)
		self.SourceTestButton = wx.Button(self.BadIdChoicesContainer, label='Test Source URL')
		self.SourceTestButtonTip = wx.ToolTip('Attempt to make an HTTP request with the source as a URL, then print the result.')
		self.SourceTestUserAgent = q.UserAgent
		self.BadIdChoicesLabel = wx.StaticText(self.BadIdChoicesContainer, style= wx.ALIGN_CENTER)
		self.BadIdChoicesLabelTip = wx.ToolTip("The status of the request performed by the 'Test Source URL' button.")
		self.BadIdChoices = ArbitraryCheckQuestion(self.BadIdChoicesContainer, TagsTracker)
		self.BadIdChoicesTip = wx.ToolTip('Pick tags set by SOURCE_QUESTION_BAD_ID_TAGS, primarily meant to be used to record issues with the source and its accessibility.')
		self.PathFormatButton = wx.Button(self, label='->')
		self.PathFormatReplaceText = wx.StaticText(self, label='Replace')
		self.PathFormatPatternEntry = wx.SearchCtrl(self, style= wx.TE_NOHIDESEL)
		self.PathFormatPatternMenu = wx.Menu()
		self.PathFormatWithText = wx.StaticText(self, label=' with')
		self.PathFormatReplaceEntry = wx.SearchCtrl(self, style= wx.TE_NOHIDESEL)
		self.PathFormatReplaceMenu = wx.Menu()
		self.BulkSourceButton = wx.Button(self, label='Bulk Apply Source')
		self.BulkSourceButtonTip = wx.ToolTip('Apply the current source to all selected image indices.')
		self.NumberChooser = PathNumberChooser(self, OutputFiles)
		self._SetBulkSourceButtonState()
		#TODO: Autocomplete for these fields?
		self.PathFormatButtonTip = wx.ToolTip('Replace all Python regex backreferences in the source field with the corresponding groups.')
		self.PathFormatPatternEntryTip = wx.ToolTip('Enter the Python regex which will be matched against the path of the current image. If this cannot be matched against the string, replacement will be disabled.')
		self.PathFormatReplaceEntryTip = wx.ToolTip('Enter the Python regex backreferences that will replace the pattern.')
		self.PathFormatReplacement = None
		self._SetPathFormatButtonState()

		self.PathFormatPatternEntry.SetMenu(self.PathFormatPatternMenu)
		self.PathFormatPatternEntry.ShowSearchButton(False)
		self.PathFormatReplaceEntry.SetMenu(self.PathFormatReplaceMenu)
		self.PathFormatReplaceEntry.ShowSearchButton(False)

		#TODO: Rewrite?
		for v in q.DefaultPattern:
			self._AddPathFormatMenuItem(v, self.PathFormatPatternMenu, self._OnPathFormatPatternMenuItemChosen)
		for v in q.DefaultReplacement:
			self._AddPathFormatMenuItem(v, self.PathFormatReplaceMenu, self._OnPathFormatReplaceMenuItemChosen)

		self.EntrySizer = wx.BoxSizer(wx.HORIZONTAL)
		self.SourceChoicesLabelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.BadIdChoicesLabelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.SourceChoicesContainerSizer = wx.BoxSizer(wx.VERTICAL)
		self.BadIdChoicesContainerSizer = wx.BoxSizer(wx.VERTICAL)
		self.SourceChoicesSizer = wx.BoxSizer(wx.VERTICAL)
		self.PathFormatSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.BulkSourcerSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.MainSizer = wx.BoxSizer(wx.VERTICAL)

		self.entry.SetToolTip(self.EntryTip)
		self.RomanizeButton.SetToolTip(self.RomanizeButtonTip)
		self.SourceTestButton.SetToolTip(self.SourceTestButtonTip)
		self.SourceSearchButton.SetToolTip(self.SourceSearchButtonTip)
		self.SourceChoicesLabel.SetToolTip(self.SourceChoicesLabelTip)
		self._SetSourceChoicesTip()
		self.BadIdChoicesLabel.SetToolTip(self.BadIdChoicesLabelTip)
		self.BadIdChoices.SetToolTip(self.BadIdChoicesTip)
		self.PathFormatPatternEntry.SetToolTip(self.PathFormatPatternEntryTip)
		self.PathFormatReplaceEntry.SetToolTip(self.PathFormatReplaceEntryTip)
		self.PathFormatButton.SetToolTip(self.PathFormatButtonTip)
		self.BulkSourceButton.SetToolTip(self.BulkSourceButtonTip)

		self.SourceChoicesLabelSizer.AddStretchSpacer(1)
		self.SourceChoicesLabelSizer.Add(self.SourceChoicesLabel, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SourceChoicesLabelSizer.AddStretchSpacer(1)

		self.BadIdChoicesLabelSizer.AddStretchSpacer(1)
		self.BadIdChoicesLabelSizer.Add(self.BadIdChoicesLabel, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.BadIdChoicesLabelSizer.AddStretchSpacer(1)

		self.SourceChoicesSizer.Add(self.SourceChoices, 1, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SourceChoicesScrollable.SetSizer(self.SourceChoicesSizer)

		self.SourceChoicesContainerSizer.Add(self.SourceSearchButton, 0, wx.ALIGN_CENTER | wx.CENTER | wx.SHAPED)
		self.SourceChoicesContainerSizer.AddStretchSpacer(1)
		self.SourceChoicesContainerSizer.Add(self.SourceChoicesLabelSizer, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SourceChoicesContainerSizer.AddStretchSpacer(1)
		self.SourceChoicesContainerSizer.Add(self.SourceChoicesScrollable, 35, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SourceChoicesContainer.SetSizer(self.SourceChoicesContainerSizer)

		self.BadIdChoicesContainerSizer.Add(self.SourceTestButton, 0, wx.ALIGN_CENTER | wx.CENTER | wx.SHAPED)
		self.BadIdChoicesContainerSizer.AddStretchSpacer(1)
		self.BadIdChoicesContainerSizer.Add(self.BadIdChoicesLabelSizer, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.BadIdChoicesContainerSizer.AddStretchSpacer(1)
		self.BadIdChoicesContainerSizer.Add(self.BadIdChoices, 35, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.BadIdChoicesContainer.SetSizer(self.BadIdChoicesContainerSizer)

		self.EntrySizer.Add(self.entry, 100, wx.ALIGN_CENTER | wx.EXPAND)
		self.EntrySizer.AddStretchSpacer(1)
		self.EntrySizer.Add(self.RomanizeButton, 0, wx.ALIGN_CENTER | wx.CENTER | wx.SHAPED)

		self.PathFormatSizer.Add(self.PathFormatButton, 0, wx.ALIGN_CENTER)
		self.PathFormatSizer.AddStretchSpacer(1)
		self.PathFormatSizer.Add(self.PathFormatReplaceText, 0, wx.ALIGN_CENTER)
		self.PathFormatSizer.AddStretchSpacer(1)
		self.PathFormatSizer.Add(self.PathFormatPatternEntry, 60, wx.ALIGN_CENTER | wx.EXPAND)
		self.PathFormatSizer.AddStretchSpacer(1)
		self.PathFormatSizer.Add(self.PathFormatWithText, 0, wx.ALIGN_CENTER)
		self.PathFormatSizer.AddStretchSpacer(1)
		self.PathFormatSizer.Add(self.PathFormatReplaceEntry, 60, wx.ALIGN_CENTER | wx.EXPAND)

		self.BulkSourcerSizer.Add(self.BulkSourceButton, 0, wx.CENTER | wx.ALIGN_CENTER)
		self.BulkSourcerSizer.AddStretchSpacer(1)
		self.BulkSourcerSizer.Add(self.NumberChooser.PathEntryLabel, 0, wx.CENTER | wx.ALIGN_CENTER)
		self.BulkSourcerSizer.AddStretchSpacer(1)
		self.BulkSourcerSizer.Add(self.NumberChooser.PathEntry.entry, 50, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)
		self.BulkSourcerSizer.AddStretchSpacer(1)
		self.BulkSourcerSizer.Add(self.NumberChooser.NumberEntryLabel, 0, wx.CENTER | wx.ALIGN_CENTER)
		self.BulkSourcerSizer.AddStretchSpacer(1)
		self.BulkSourcerSizer.Add(self.NumberChooser.NumberEntry, 50, wx.CENTER | wx.ALIGN_CENTER | wx.EXPAND)

		self.MainSizer.AddStretchSpacer(2)
		self.MainSizer.Add(self.EntrySizer, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(2)
		self.MainSizer.Add(self.PathFormatSizer, 0, wx.ALIGN_CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(2)
		self.MainSizer.Add(self.BulkSourcerSizer, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.MainSizer.AddStretchSpacer(2)
		self.MainSizer.Add(self.DisplaySplitter, 55, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SetSizer(self.MainSizer)

		self.NumberChooser.PathEntry.SelfBinds()
		self.NumberChooser.SelfBinds()
		self.Bind( wx.EVT_BUTTON, self._OnBulkSourceButton, id=self.BulkSourceButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnNumberEntry, id=self.NumberChooser.NumberEntry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnRomanize, id=self.RomanizeButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnChange, id=self.entry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnPathFormatButton, id=self.PathFormatButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnSourceTestButton, id=self.SourceTestButton.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnSourceSearchButton, id=self.SourceSearchButton.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnPathFormatEntry, id=self.PathFormatPatternEntry.GetId() )
		self.Bind( wx.EVT_TEXT, self._OnPathFormatEntry, id=self.PathFormatReplaceEntry.GetId() )
		self.Bind( wx.EVT_RADIOBOX, self._OnSourceChoices, id=self.SourceChoices.GetId() )
		self.Bind( wx.EVT_SIZE, self._OnSourceChoicesContainerSize, id=self.SourceChoicesContainer.GetId() )
		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")

		self.SourceChoicesScrollable.SetOwnBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) )
		self.SourceChoicesScrollable.SetupScrolling()
		self.BadIdChoices.SetChoices(q.BadIdTags)
		self.DisplaySplitter.SetMinimumPaneSize( self.GetSize().GetWidth() )
		self.DisplaySplitter.SplitVertically(self.SourceChoicesContainer, self.BadIdChoicesContainer)
		self.BadIdChoicesContainer.SetMaxSize( self.SourceChoicesContainer.GetSize() )

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
		self.ChoicesTip = wx.ToolTip("Set safety rating here.")
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.choices.SetToolTip(self.ChoicesTip)

		self.sizer.Add(self.choices, 1, wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.Bind( wx.EVT_RADIOBOX, self._OnSelect, id=self.choices.GetId() )

		self.SetOwnBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW) )
		self.SetupScrolling()

class BlankQuestion(wx.Panel):
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		pass
	def clear(self):
		pass
	def disp(self):
		pass
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.MsgSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.msg = wx.StaticText(self, label='This question is blank.')

		self.MsgSizer.AddStretchSpacer(1)
		self.MsgSizer.Add(self.msg, 0, wx.ALIGN_CENTER)
		self.MsgSizer.AddStretchSpacer(1)
		self.sizer.Add(self.MsgSizer, 1, wx.ALIGN_CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		#self.tooltip = wx.ToolTip("This question is blank.")
		#self.SetToolTip(self.tooltip)

class TagChecker(wx.Panel):
	def UpdateChoices(self):
		self.finder.FindNames() # TODO: Handle this in a callback local to the class?
		self.display.ChangeValue( '\n'.join(self.finder.FoundNames) )
	def _OnFindButton(self, e):
		self.UpdateChoices()
		e.Skip()
	def _OnEntryChange(self, e):
		self.finder.SetUpdateNeeded()
		e.Skip()
	def load(self, OutputFile):
		"Initialize the question for a certain case."
		pass
	def clear(self):
		"Clear the question for the given case."
		pass
	def disp(self):
		"Display the updated question for the given case."
		self.finder.disp()
	#def _OnFileUpdatePending(self, message, arg2=None):
	#	wx.CallAfter(self.first.SetUpdateNeeded)
	def __init__(self, parent, TagsTracker, q):
		wx.Panel.__init__(self, parent=parent)

		self.finder = SimilarTagsFinder(self, TagsTracker)
		self.display = wx.TextCtrl(self, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_NOHIDESEL)
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.finder, 0, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.sizer.AddStretchSpacer(1)
		self.sizer.Add(self.display, 100, wx.ALIGN_CENTER | wx.CENTER | wx.EXPAND)
		self.SetSizer(self.sizer)

		self.FinderTip = wx.ToolTip("Determine how similar tags should be found, here.")
		self.finder.SetToolTip(self.FinderTip)
		self.DisplayTip = wx.ToolTip("Tags found by the search are here. Not editable.")
		self.display.SetToolTip(self.DisplayTip)

		self.Bind( wx.EVT_TEXT, self._OnEntryChange, id=self.finder.SeparatorsEntry.GetId() )
		self.Bind( wx.EVT_BUTTON, self._OnFindButton, id=self.finder.FindButton.GetId() )

		#pub.subscribe(self._OnFileUpdatePending, "FileUpdatePending")

		self.finder.SeparatorsEntry.SetValue(q.DefaultSeparators)

class CopyableCustomTags(CustomTags):
	def __init__(self, parent, DefaultTags, TagsTracker, OutputFiles):
		SplitterBase.__init__(self, parent=parent, style=wx.SP_LIVE_UPDATE)

		self.first = StoragelessEntry(self)
		self.second = ToggleCopyArbitraryCheckQuestion(self, TagsTracker, OutputFiles)

		self.EntryTip = wx.ToolTip("Enter tags here. They will be displayed to the right.")
		self.first.entry.SetToolTip(self.EntryTip)
		self.second.ChoicesTipText = "Select tags to be written to file, here."
		self.second.SetChoicesTip()

		self.SetMinimumPaneSize( self.GetSize().GetWidth() )
		self.SplitVertically(self.first, self.second)

		self.Bind( wx.EVT_TEXT, self._OnEntryChange, id=self.first.entry.GetId() )

		self.first.entry.SetValue(DefaultTags)

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
	def _ShiftImage(self, func):
		if self.LockQuestion:
			idx = self.positions[self.pos.get()].get()
			self._hide()
			func()
			self._LoadAll()
			self.positions[self.pos.get()].set(idx)
			self._disp()
		else:
			self._hide()
			func()
			self._LoadAll()
			self._disp()
	def _OnIndexImage(self, message, arg2=None):
		"Change the index index to the one specified in the event, if possible."
		# TODO: Streamline this to avoid a comparison that happens in the CircularCounter
		if 0 <= message <= self.pos.GetMax():
			self._ShiftImage( lambda self=self, message=message: self.pos.set(message) )
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the positions array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._ShiftImage(self.pos.dec)
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the positions array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._ShiftImage(self.pos.inc)
	def _OnIndexQuestion(self, message, arg2=None):
		"Change the question index to the one specified in the message, if possible."
		# TODO: Streamline this to avoid a comparison that happens in the CircularCounter
		if 0 <= message <= self.positions[self.pos.get()].GetMax():
			self._hide()
			self.positions[self.pos.get()].set(message)
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
	def _OnLockQuestion(self, message, arg2=None):
		"Set the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = True
	def _OnUnlockQuestion(self, message, arg2=None):
		"Unset the variable which will decide whether to use the question index of the previous image, when changing images."
		self.LockQuestion = False
	def _OnFocusQuestionBody(self, message, arg2=None):
		self._CurrentWidget().SetFocus()
	def __init__(self, parent, TagsTracker, questions, OutputFiles, images):
		wx.Panel.__init__(self, parent=parent)

		NumImages = len(OutputFiles.InputPaths)

		self.NumQuestions = len(questions)
		self.LockQuestion = False
		self.pos = CircularCounter(len(OutputFiles.InputPaths) - 1) # The position in positions
		self.positions = [CircularCounter(self.NumQuestions - 1) for i in OutputFiles.InputPaths] # The position in questions corresponding to each image

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
				self.QuestionWidgets.append( EntryQuestion(self, NumImages, TagsTracker) )
			elif q.type == QuestionType.SESSION_TAGS:
				self.QuestionWidgets.append( SessionTags(self, TagsTracker) )
			elif q.type == QuestionType.NAME_QUESTION:
				self.QuestionWidgets.append( NameQuestion(self, TagsTracker) )
				proportion = 0
			elif q.type == QuestionType.SOURCE_QUESTION:
				self.QuestionWidgets.append( SourceQuestion(self, q, OutputFiles.ControlFiles, TagsTracker, images) )
				#proportion = 0
			elif q.type == QuestionType.SAFETY_QUESTION:
				self.QuestionWidgets.append( SafetyQuestion(self) )
			elif q.type == QuestionType.IMAGE_TAGS_ENTRY:
				self.QuestionWidgets.append( ImageTagsEntry(self, TagsTracker) )
			elif q.type == QuestionType.SESSION_TAGS_IMPORTER:
				self.QuestionWidgets.append( SessionTagsImporter(self, OutputFiles.ControlFiles, TagsTracker) )
			elif q.type == QuestionType.BULK_TAGGER:
				self.QuestionWidgets.append( BulkTagger(self, OutputFiles.ControlFiles, TagsTracker) )
			elif q.type == QuestionType.ADDED_TAGS:
				self.QuestionWidgets.append( AddedTags(self, TagsTracker) )
			elif q.type == QuestionType.ADDED_TAGS_ENTRY:
				self.QuestionWidgets.append( AddedTagsEntry(self, NumImages, OutputFiles, TagsTracker) )
			elif q.type == QuestionType.CUSTOM_TAGS:
				self.QuestionWidgets.append( CustomTags(self, q.DefaultTags, TagsTracker) )
			elif q.type == QuestionType.BLANK_QUESTION:
				self.QuestionWidgets.append( BlankQuestion(self) )
			elif q.type == QuestionType.NATIVE_TAGS:
				self.QuestionWidgets.append( NativeTags(self, TagsTracker) )
			elif q.type == QuestionType.TAG_CHECKER:
				self.QuestionWidgets.append( TagChecker(self, TagsTracker, q) )
			elif q.type == QuestionType.COPYABLE_CUSTOM_TAGS:
				self.QuestionWidgets.append( CopyableCustomTags(self, q.DefaultTags, TagsTracker, OutputFiles.ControlFiles) )
			else:
				#TODO: Rewrite?
				raise ValueError() # We should never get this.
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
		pub.subscribe(self._OnLockQuestion, "LockQuestion")
		pub.subscribe(self._OnUnlockQuestion, "UnlockQuestion")
