"Reusable GUI components which may be imported by any other GUI component."

from os.path import commonprefix

import wx
from pubsub import pub

def GetPreviewText(i, v):
	IndexText = str(i + 1)
	divider = " : "
	LenDiff = 80 - len(IndexText) - len(divider)
	end = ""
	if len(v) > LenDiff:
		end = "..."
	trimmed = v[:LenDiff - len(end)].replace('\r\n', ' ').replace('\n', ' ')
	return ''.join( (IndexText, divider, trimmed, end) )

def RenderThreeIfMid(pre, mid, post):
	if mid and isinstance(mid, str):
		return ''.join( (pre, mid, post) )
	else:
		return ''

class CircularCounter:
	def set(self, value):
		"Change the value to the one specified, if possible."
		if 0 <= value <= self._MaxValue:
			self._value = value
			return True
		else:
			return False
	def get(self):
		"Get the current value."
		return self._value
	def GetMax(self):
		"Get the maximum value."
		return self._MaxValue
	def _CalcDec(self):
		if self._value == 0:
			return self._MaxValue
		else:
			return self._value - 1
	def _CalcInc(self):
		if self._value >= self._MaxValue:
			return 0
		else:
			return self._value + 1
	def dec(self):
		"Decrement the value if it is greater than 0. Otherwise, loop around to the maximum value."
		self._value = self._CalcDec()
	def inc(self):
		"Increment the value if it is less than the maximum value. Otherwise, loop around to 0."
		self._value = self._CalcInc()
	def PeekDec(self):
		return self._CalcDec()
	def PeekInc(self):
		return self._CalcInc()
	def __init__(self, MaxValue):
		self._MaxValue = MaxValue
		self._value = 0

class SearchEntry: # This class should never be used on its own
	def GetValue(self):
		"Get the current value of the entry."
		return self.entry.GetValue()
	def write(self, text):
		self.entry.write(text)
	def IsEmpty(self):
		return self.entry.GetValue() == ""
	def Clear(self):
		self.entry.Clear()
	def SetEntryTip(self):
		if self.EntryTipText is not None:
			self.entry.UnsetToolTip()
			self.entry.SetToolTip( wx.ToolTip(self.EntryTipText) )
	def FocusEntry(self):
		self.entry.SetFocus()
	def FocusMenu(self):
		self.UpdateMenu()
		self.entry.PopupMenu(self._menu)
	#TODO SKIP?
	def _OnFocusEntry(self, message, arg2=None):
		self.FocusEntry()
	#TODO SKIP?
	def _OnFocusMenu(self, message, arg2=None):
		self.FocusMenu()
	def _OnSearch(self, e):
		self.UpdateMenu()
		e.Skip()
	def _OnMenuItemChosen(self, e):
		self.ChooseMenuItem( e.GetId() )
		e.Skip()
	def UpdateAutocomplete(self):
		val = self.entry.GetValue()
		TrueOrig = val
		orig = TrueOrig.lower()
		ContainsOrig = []
		prefixes = []
		for s in self.GetAutocompleteOptions():
			sLower = s.lower()
			if orig in sLower:
				ContainsOrig.append(s)
			if val.lower() in sLower:
				if len(s) > len(val):
					val = s
			else:
				prefixes.append( commonprefix([s, val]) )
		if len(ContainsOrig) == 1:
			val = ContainsOrig[0]
		else:
			prefixes = tuple( (p for p in prefixes if p) )
			MaxPrefixLen = len( max(prefixes, key=len) )
			MaxPrefixes = tuple( (p for p in prefixes if len(p) == MaxPrefixLen) )
			if len(MaxPrefixes) == 1:
				val = MaxPrefixes[0]
			else:
				val = TrueOrig
		self.entry.SetValue(val)

class PathEntry(SearchEntry):
	def SetPath(self, pos):
		"Set the path label to show the path at pos in the paths array, and the index label to show pos + 1 out of length of paths array."
		self.entry.SetValue(self._paths[pos])
	def UpdateMenu(self):
		"Set the contents of PathMenu based on the contents of PathEntry."
		_menu = self._menu
		_MenuItems = self._MenuItems
		Remove = _menu.Remove
		Append = _menu.Append
		for i in _menu.GetMenuItems():
			Remove(i)
		EntryValue = self.entry.GetValue()
		AddAll = False
		if EntryValue in self._paths:
			AddAll = True
		for i, s in enumerate(self._paths):
			if AddAll or EntryValue in s:
				Append(_MenuItems[i])
	def GetAutocompleteOptions(self):
		return self._paths
	def ChooseMenuItem(self, ItemId):
		"Set the path entry to the chosen menu value."
		self.entry.SetValue(self._MenuLookup[ItemId])
	def GetPathsLen(self):
		return self._PathsLen
	def SearchPath(self, query):
		return self._paths.index(query)
	def SelfBinds(self):
		for i in self._MenuItems:
			self.parent.Bind( wx.EVT_MENU, self._OnMenuItemChosen, id=i.GetId() )

		self.parent.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self._OnSearch, id=self.entry.GetId() )
	def SelfPubSub(self):
		pub.subscribe(self._OnFocusEntry, "FocusPathName")
		pub.subscribe(self._OnFocusMenu, "FocusPathNameMenu")
	def __init__(self, parent, paths):
		self._paths = paths
		self._PathsLen = len(self._paths)
		self._MenuItems = []
		self._MenuLookup = {}
		self._menu = wx.Menu()
		self.parent = parent
		self.entry = wx.SearchCtrl(parent, style= wx.TE_LEFT | wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Search box containing path of current image
		#TODO: Tab completion for these fields?
		self.EntryTipText = "Image path entry; if the path doesn't exist, then press enter autocomplete."

		self.SetEntryTip()

		for i, p in enumerate(self._paths):
			ItemId = wx.NewId()
			PreviewText = GetPreviewText(i, p)
			item = wx.MenuItem(self._menu, ItemId, PreviewText, PreviewText)
			self._MenuItems.append(item)
			self._MenuLookup[ItemId] = p
		self.entry.SetMenu(self._menu)
		self.entry.ShowSearchButton(False)
		self.SetPath(0)

class TagSearch(SearchEntry):
	def ForcePendingUpdate(self):
		self._MenuUpdated = False
	def _EnableButtons(self, status):
		self.LeftImage.Enable(status)
		self.RightImage.Enable(status)
	def UpdateMenu(self):
		if self._MenuUpdated:
			return
		_menu = self._menu
		_MenuItems = self._MenuItems
		Remove = _menu.Remove
		Append = _menu.Append
		for i in _menu.GetMenuItems():
			Remove(i)
		EntryValues = self.entry.GetValue().lower().split()
		AddAll = False
		EnableButtons = False
		if not EntryValues:
			AddAll = True
		for i, f in enumerate(self._OutputFiles.ControlFiles):
			f.lock()
			AddV = False
			for v in EntryValues:
				if AddAll:
					break
				elif f.tags.has(v) or\
					 ( v.startswith('-') and not f.tags.has(v[1:]) ):
					AddV = True
				else:
					AddV = False
					break
			if AddAll or AddV:
				Append(_MenuItems[i])
				EnableButtons = True
			f.unlock()
		self._EnableButtons(EnableButtons)
		self._MenuUpdated = True
	def CheckForAnyMatches(self):
		EntryValues = self.entry.GetValue().lower().split()
		EnableButtons = False
		if not EntryValues:
			EnableButtons = True
		else:
			for i, f in enumerate(self._OutputFiles.ControlFiles):
				if i == self.pos.get():
					continue
				f.lock()
				AddV = False
				for v in EntryValues:
					if f.tags.has(v) or\
					   ( v.startswith('-') and not f.tags.has(v[1:]) ):
						AddV = True
					else:
						AddV = False
						break
				if AddV:
					EnableButtons = True
					f.unlock()
					break
				f.unlock()
		self._EnableButtons(EnableButtons)
	def ChooseMenuItem(self, i):
		pub.sendMessage("IndexImage", message=self._MenuLookup[i])
	def _OnLeftImageButton(self, e):
		pub.sendMessage("LeftTagSearchImage", message=None)
		e.Skip()
	def _OnRightImageButton(self, e):
		pub.sendMessage("RightTagSearchImage", message=None)
		e.Skip()
	def _OnEntry(self, e):
		self._MenuUpdated = False
		self.CheckForAnyMatches()
		e.Skip()
	def SelfBinds(self):
		for i in self._MenuItems:
			self.parent.Bind( wx.EVT_MENU, self._OnMenuItemChosen, id=i.GetId() )

		self.parent.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self._OnSearch, id=self.entry.GetId() )
		self.parent.Bind( wx.EVT_BUTTON, self._OnLeftImageButton, id=self.LeftImage.GetId() )
		self.parent.Bind( wx.EVT_BUTTON, self._OnRightImageButton, id=self.RightImage.GetId() )
		self.parent.Bind( wx.EVT_TEXT, self._OnEntry, id=self.entry.GetId() )
	def _OnIndexImage(self, message, arg2=None):
		"Change the image index to the one specified in the event, if possible."
		self._MenuUpdated = False
		self.pos.set(message)
		self.CheckForAnyMatches()
	def _OnLeftImage(self, message, arg2=None):
		"Shift to the left (-1) position to the current pos in the images array if the pos is greater than 0. Otherwise, loop around to the last item."
		self._MenuUpdated = False
		self.pos.dec()
		self.CheckForAnyMatches()
	def _OnRightImage(self, message, arg2=None):
		"Shift to the right (+1) position to the current pos in the images array if the pos is less than the length of the positions array. Otherwise, loop around to the first item."
		self._MenuUpdated = False
		self.pos.inc()
		self.CheckForAnyMatches()
	def _OnLeftResult(self, message, arg2=None):
		"Go to the left (previously) available search result, given the current image."
		self.UpdateMenu()
		pos = self.pos.get()
		items = self._menu.GetMenuItems()
		left = None
		for i in items:
			current = self._MenuLookup[i.GetId()]
			if pos <= current:
				break
			left = current
		if left is None and len(items) > 0:
			left = self._MenuLookup[items[-1].GetId()]
		if left is not None:
			pub.sendMessage("IndexImage", message=left)
			self.LeftImage.SetFocus()
	def _OnRightResult(self, message, arg2=None):
		"Go to the right (next) available search result, given the current image."
		self.UpdateMenu()
		pos = self.pos.get()
		items = self._menu.GetMenuItems()
		right = None
		chosen = None
		for i in items:
			right = self._MenuLookup[i.GetId()]
			if pos < right:
				chosen = right
				break
		if chosen is None and len(items) > 0:
			chosen = self._MenuLookup[items[0].GetId()]
		if chosen is not None:
			pub.sendMessage("IndexImage", message=chosen)
			self.RightImage.SetFocus()
	def _OnFileUpdate(self, message, arg2=None):
		wx.CallAfter(self.CheckForAnyMatches)
	def SelfPubSub(self):
		pub.subscribe(self._OnFocusEntry, "FocusTagSearch")
		pub.subscribe(self._OnFocusMenu, "FocusTagSearchMenu")
		pub.subscribe(self._OnIndexImage, "IndexImage")
		pub.subscribe(self._OnLeftImage, "LeftImage")
		pub.subscribe(self._OnRightImage, "RightImage")
		pub.subscribe(self._OnLeftResult, "LeftTagSearchImage")
		pub.subscribe(self._OnRightResult, "RightTagSearchImage")
		pub.subscribe(self._OnFileUpdate, "FileUpdatePending")
		pub.subscribe(self._OnFileUpdate, "FileUpdateClear")
	def __init__(self, parent, OutputFiles):
		self._OutputFiles = OutputFiles
		self._MenuItems = []
		self._MenuLookup = {}
		self._MenuUpdated = False
		self._menu = wx.Menu()
		self.parent = parent
		self.pos = CircularCounter( len(self._OutputFiles.InputPaths) - 1 ) # The current image.
		self.entry = wx.SearchCtrl(parent, style= wx.TE_NOHIDESEL) # Search box containing space-separated tags to search for.
		self.LeftImage = wx.Button(parent, label = '<', style=wx.BU_EXACTFIT)
		self.RightImage = wx.Button(parent, label = '>', style=wx.BU_EXACTFIT)
		self.EntryTipText = "Tag search field. Enter space-separated tags to update menu. Menu items will switch to the associated image."
		self.LeftImageTip = wx.ToolTip("Previous image in search results.")
		self.RightImageTip = wx.ToolTip("Next image in search results.")

		self.SetEntryTip()

		if len(self._OutputFiles.InputPaths) <= 1:
			self.LeftImage.Disable()
			self.RightImage.Disable()

		self.SetEntryTip()
		self.LeftImage.SetToolTip(self.LeftImageTip)
		self.RightImage.SetToolTip(self.RightImageTip)

		for i, p in enumerate(OutputFiles.InputPaths):
			ItemId = wx.NewId()
			PreviewText = GetPreviewText(i, p)
			item = wx.MenuItem(self._menu, ItemId, PreviewText, PreviewText)
			self._MenuItems.append(item)
			self._MenuLookup[ItemId] = i
		self.entry.SetMenu(self._menu)
		self.entry.ShowSearchButton(False)

class TagLookup(SearchEntry):
	def UpdateMenu(self):
		"Set the contents of PathMenu based on the contents of PathEntry."
		for i in self._MenuItems:
			self.parent.Unbind( wx.EVT_MENU, id=i.GetId() )
		for i in self._menu.GetMenuItems():
			self._menu.Remove(i)
		self._MenuItems = []
		self._MenuLookup = {}
		results = self.TagsTracker.FindFuzzyDict( self.entry.GetValue().strip() )
		results = sorted(results.items(), key=lambda i: i[1], reverse=True)
		for r in results:
			ItemId = wx.NewId()
			PreviewText = ''.join( ( r[0], ' : ', str(r[1]) ) )
			item = wx.MenuItem(self._menu, ItemId, PreviewText, PreviewText)
			self._MenuItems.append(item)
			self._MenuLookup[ItemId] = r[0]
			self.parent.Bind(wx.EVT_MENU, self.ItemCallback, id=ItemId)
			self._menu.Append(item)
	def UpdateAutocomplete(self):
		val = self.entry.GetValue().lower()
		orig = val.lower()
		ContainsOrig = []
		StartsWithOrig = []
		prefixes = []
		for s in self.GetAutocompleteOptions():
			if orig in s:
				ContainsOrig.append(s)
				if s.startswith(orig):
					StartsWithOrig.append(s)
			if val in s:
				if len(s) > len(val):
					val = s
			else:
				prefixes.append( commonprefix([s, val]) )
		if len(ContainsOrig) == 1:
			val = ContainsOrig[0]
		elif len(StartsWithOrig) > 0:
			val = commonprefix(StartsWithOrig)
		else:
			prefixes = tuple( (p for p in prefixes if p) )
			if len(prefixes) > 0:
				val = max(prefixes, key=len)
			else:
				val = orig
		self.entry.SetValue(val)
	def GetAutocompleteOptions(self):
		return self.TagsTracker.FindFuzzy( self.entry.GetValue().strip() )
	def GetMenuItem(self, ItemId):
		"Set the path entry to the chosen menu value."
		return self._MenuLookup[ItemId]
	def SelfBinds(self):
		self.parent.Bind( wx.EVT_SEARCHCTRL_SEARCH_BTN, self._OnSearch, id=self.entry.GetId() )
	def SelfPubSub(self):
		pub.subscribe(self._OnFocusEntry, "FocusTagLookup")
		pub.subscribe(self._OnFocusMenu, "FocusTagLookupMenu")
	def __init__(self, parent, ItemCallback, TagsTracker):
		self.TagsTracker = TagsTracker
		self._MenuItems = []
		self._MenuLookup = {}
		self._menu = wx.Menu()
		self.parent = parent
		self.ItemCallback = ItemCallback
		self.entry = wx.SearchCtrl(parent, style= wx.TE_LEFT | wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Search box containing path of current image
		self.EntryTipText = "This search menu lists all tags which contain the entered text. Press enter for autocomplete."

		self.SetEntryTip()

		self.entry.SetMenu(self._menu)
		self.entry.ShowSearchButton(False)
