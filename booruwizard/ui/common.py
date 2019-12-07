"Reusable GUI components which may be imported by any other GUI component."

from os.path import commonprefix

import wx

class PathEntry:
	def SetPath(self, pos):
		"Set the path label to show the path at pos in the paths array, and the index label to show pos + 1 out of length of paths array."
		self.entry.SetValue(self._paths[pos])
	def GetPath(self):
		"Get the current value of the entry."
		self.entry.GetValue()
	def GetEntryId(self):
		"Get the ID of the path entry field."
		return self._entry.GetId()
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
		for i, s in enumerate(self._paths):
			if EntryValue in s:
				Append(_MenuItems[i])
	def UpdateAutocomplete(self):
		"Try to autocomplete the contents of the path entry to a complete string."
		val = self._entry.GetValue()
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
			val = max(prefixes, key=len)
		self._entry.SetValue(val)
	def ChooseMenuItem(self, ItemId):
		"Set the path entry to the chosen menu value."
		self._entry.SetValue(self._MenuLookup[ItemId])
	def FocusEntry(self):
		self.PathEntry.SetFocus()
	def FocusMenu(self):
		self._UpdatePathMenu()
		self.PathEntry.PopupMenu(self.PathMenu)
	def GetPathsLen(self):
		return self._PathsLen
	def SearchPath(self, query):
		return self._paths.index(query)
	def __init__(self, paths):
		self._paths = paths
		self._PathsLen = len(self._paths)
		self._MenuItems = []
		self._MenuLookup = {}
		self._menu = wx.Menu()
		self._entry = wx.SearchCtrl(self, style= wx.TE_LEFT | wx.TE_PROCESS_ENTER | wx.TE_NOHIDESEL) # Search box containing path of current image
		self._EntryTip = wx.ToolTip("Image path entry; if the path doesn't exist, then autocomplete.")

		self._entry.SetToolTip(self._EntryTip)

		for p in self._paths:
			ItemId = wx.NewId()
			item = wx.MenuItem(self.PathMenu, ItemId, p, p)
			self._MenuItems.append(item)
			self._MenuLookup[ItemId] = p
			self.Bind(wx.EVT_MENU, self._OnMenuPathChosen, id=ItemId)
		self._entry.SetMenu(self._menu)
		self._entry.ShowSearchButton(False)
		self.SetPath(0)
