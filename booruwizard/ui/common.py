"Reusable GUI components which may be imported by any other GUI component."

from os.path import commonprefix

import wx

def GetPreviewText(i, v):
	IndexText = str(i + 1)
	divider = " : "
	LenDiff = 80 - len(IndexText) - len(divider)
	end = ""
	if len(v) > LenDiff:
		end = "..."
	trimmed = v[:LenDiff - len(end)].replace('\r\n', ' ').replace('\n', ' ')
	return ''.join( (IndexText, divider, trimmed, end) )

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
	def dec(self):
		"Decrement the value if it is greater than 0. Otherwise, loop around to the maximum value."
		if self._value == 0:
			self._value = self._MaxValue
		else:
			self._value -= 1
	def inc(self):
		"Increment the value if it is less than the maximum value. Otherwise, loop around to 0."
		if self._value >= self._MaxValue:
			self._value = 0
		else:
			self._value += 1
	def __init__(self, MaxValue):
		self._MaxValue = MaxValue
		self._value = 0

class PathEntry:
	def SetPath(self, pos):
		"Set the path label to show the path at pos in the paths array, and the index label to show pos + 1 out of length of paths array."
		self.entry.SetValue(self._paths[pos])
	def GetPath(self):
		"Get the current value of the entry."
		return self.entry.GetValue()
	def GetMenuItemIds(self):
		"Return a list of IDs for each menu item."
		output = []
		for i in self._MenuItems:
			output.append( i.GetId() )
		return output
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
	def UpdateAutocomplete(self):
		"Try to autocomplete the contents of the path entry to a complete string."
		val = self.entry.GetValue()
		orig = val.lower()
		ContainsOrig = []
		prefixes = []
		for s in self._paths:
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
			val = max(prefixes, key=len)
		self.entry.SetValue(val)
	def ChooseMenuItem(self, ItemId):
		"Set the path entry to the chosen menu value."
		self.entry.SetValue(self._MenuLookup[ItemId])
	def FocusEntry(self):
		self.entry.SetFocus()
	def FocusMenu(self):
		self.UpdateMenu()
		self.entry.PopupMenu(self._menu)
	def GetPathsLen(self):
		return self._PathsLen
	def SearchPath(self, query):
		return self._paths.index(query)
	def __init__(self, parent, paths):
		self._paths = paths
		self._PathsLen = len(self._paths)
		self._MenuItems = []
		self._MenuLookup = {}
		self._menu = wx.Menu()
		self.entry = wx.SearchCtrl(parent, style= wx.TE_LEFT | wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Search box containing path of current image
		self._EntryTip = wx.ToolTip("Image path entry; if the path doesn't exist, then press enter autocomplete.")

		self.entry.SetToolTip(self._EntryTip)

		for i, p in enumerate(self._paths):
			ItemId = wx.NewId()
			PreviewText = GetPreviewText(i, p)
			item = wx.MenuItem(self._menu, ItemId, PreviewText, PreviewText)
			self._MenuItems.append(item)
			self._MenuLookup[ItemId] = p
		self.entry.SetMenu(self._menu)
		self.entry.ShowSearchButton(False)
		self.SetPath(0)
