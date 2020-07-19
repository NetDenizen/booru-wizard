"Representations of individual image tags and containers for them."

from collections import OrderedDict
from bisect import bisect_right

class tag:
	def __init__(self, name):
		self.name = name # Name of tag.
		self.occurrences = 0 # Number of times a tag has occurred
		self.ConfigTag = False # This flag is registered in the configuration file.
	def sub(self, val):
		"Subtract a value from the occurrences if the outcome is greater than 0."
		occurrences = self.occurrences - val
		if occurrences >= 0:
			self.occurrences = occurrences

class TagsContainer:
	def __init__(self):
		self.lookup = {} # Lookup table for quickly locating tags
		self.names = []
		self.tags = []
	def register(self, name):
		"Add a single tag object with zero occurrences; if it already exists, then do nothing. Return the registered tag."
		lookup = self.lookup
		NameLower = name.lower()
		found = lookup.get(NameLower, None)
		if found is None:
			names = self.names
			new = tag(NameLower)
			lookup[NameLower] = new
			idx = bisect_right(names, NameLower)
			names.insert(idx, NameLower)
			self.tags.insert(idx, new)
			return new
		else:
			return found
	def RegisterConfig(self, name):
		"Register a given tag object, and set it to be a ConfigTag."
		if not name:
			return
		registered = self.register(name)
		registered.ConfigTag = True
	def set(self, name, value):
		"Register a tag object and set its occurrences to the specified value, if that value is greater than the current number of occurrences."
		if not name:
			return
		registered = self.register(name)
		if registered.occurrences < value:
			registered.occurrences = value
	def SetObj(self, obj):
		"Set a tag object in this container."
		self.set(obj.name, obj.occurrences)
	def SetStringList(self, strings, value):
		"Set a list of tags as individual strings."
		for s in strings:
			self.set(s, value)
	def SetString(self, string, value):
		"Set a list of tags as a space terminated string."
		names = string.split()
		self.SetStringList(names, value)
	def SetContainer(self, container):
		"Merge the tag objects from another TagsContainer."
		for t in container.tags:
			self.SetObj(t)
	def add(self, name, value):
		"Register a tag object and increment its occurrences by a value."
		if not name:
			return
		registered = self.register(name)
		registered.occurrences += value
	def AddStringList(self, strings, value):
		"Add a list of tags as individual strings."
		for s in strings:
			self.add(s, value)
	def AddString(self, string, value):
		"Add a list of tags as a space terminated string."
		names = string.split()
		self.AddStringList(names, value)
	def sub(self, name, value):
		"Register a tag object and decrement its occurrences by a value."
		if not name:
			return
		registered = self.register(name)
		registered.sub(value)
	def SubStringList(self, strings, value):
		"Sub a list of tags as individual strings."
		for s in strings:
			self.sub(s, value)
	def SubString(self, string, value):
		"Sub a list of tags as individual strings."
		names = string.split()
		self.SubStringList(names, value)
	def clear(self, name, value):
		"Register a tag object and set its occurrences to 0 if it is less than or equal to 0."
		if not name:
			return
		registered = self.register(name)
		if registered.occurrences <= value:
			registered.occurrences = 0
	def ClearObj(self, obj):
		"Clear a tag object in this container."
		self.clear(obj.name, obj.occurrences)
	def ClearContainer(self, container):
		"Clear the tag objects from another TagsContainer."
		for t in container.tags:
			self.ClearObj(t)
	def ClearStringList(self, strings, value):
		"Clear a list of tags as individual strings."
		for s in strings:
			self.clear(s, value)
	def ClearString(self, string, value):
		"Clear a list of tags as a space terminated string."
		names = string.split()
		self.ClearStringList(names, value)
	def has(self, name):
		return (name and name in self.lookup and self.ReturnStringOccurrences(name) > 0)
	def HasAnyOfStringList(self, strings):
		for s in strings:
			if self.has(s):
				return True
		return False
	def HasAnyOfString(self, string):
		return self.HasAnyOfStringList( string.split() )
	def HasAllOfStringList(self, strings):
		for s in strings:
			if not self.has(s):
				return False
		return True
	def HasConfigTag(self, name):
		"Determine if a ConfigTag is registered under a given name, and it has more than one occurrences."
		if not name:
			return False
		registered = self.register(name)
		if registered.occurrences > 0 and registered.ConfigTag:
			return True
		else:
			return False
	def ReturnStringList(self):
		"Return the list of tag objects with 1 or more occurrences as a list of strings."
		output = []
		for s in self.tags:
			if s.occurrences > 0:
				output.append(s.name)
		return output
	def ReturnString(self):
		"Return the list of tag objects with 1 or more occurrences as a space separated list of strings."
		return ' '.join( self.ReturnStringList() )
	def ReturnStringOccurrences(self, string):
		"Register the string and return the number of occurrences."
		if not string:
			return ""
		registered = self.register(string)
		return registered.occurrences
	def ReturnHighestOccurrences(self):
		"Return the most occurrences for any tag."
		highest = 0
		for t in self.tags:
			if t.occurrences > highest:
				highest = t.occurrences
		return highest
	def ReturnDict(self):
		"Return all tags with 1 or more occurrences as a dict with names as keys and occurrences as the values."
		output = OrderedDict()
		for t in self.tags:
			if t.occurrences > 0:
				output[t.name] = t.occurrences
		return output
	def ReturnOccurrenceStrings(self):
		"Return all tags with 1 or more occurrences, as a list of ordered space-separated strings, each representing the tags associated with each number of occurrences."
		OutputLists = []
		for t in self.tags:
			if t.occurrences < 1:
				continue
			while t.occurrences > len(OutputLists):
				OutputLists.append( list() )
			OutputLists[t.occurrences - 1].append(t.name)
		return [' '.join(l) for l in OutputLists]

class ConditionalTagger:
	def __init__(self):
		self.lookup = {} # A dictionary of tag names to correspond to containers of tags.
		self.ReverseLookup = {} # A dictionary of containers to correspond to tag names; reverse of self.lookup.
	def AddString(self, keys, tags):
		"Keys and tags are space separated lists of tags. Make it so that each key will retrieve a list of its associated tags, and vice-versa."
		#TODO: Add strings until no more added
		if not keys or not tags:
			return
		KeysList = keys.lower().split()
		TagsList = tags.lower().split()
		for k in KeysList:
			found = self.lookup.get(k, None)
			if found is None:
				self.lookup[k] = TagsList
			else:
				self.lookup[k].extend(t for t in TagsList if t not in self.lookup[k])
		for t in TagsList:
			found = self.ReverseLookup.get(t, None)
			if found is None:
				self.ReverseLookup[t] = KeysList
			else:
				self.ReverseLookup[t].extend(k for k in KeysList if k not in self.ReverseLookup[t])
	def SetTags(self, name, target):
		"Search for the name in lookup, and if it is found, then set the target container with the found one."
		if not name:
			return
		found = self.lookup.get(name.lower(), None)
		if found is not None:
			target.SetStringList(found, 1)
	def ClearTags(self, name, target):
		"Search for the name in lookup, and if it (or any other name controlling the associated tags) is found, then clear them."
		if not name:
			return
		found = self.lookup.get(name.lower(), None)
		if found is None:
			return
		for t in found:
			DoClear = True
			for k in self.ReverseLookup[t]:
				if name not in self.lookup[k]:
					break
				if target.ReturnStringOccurrences(k) > 0 and k != name:
					DoClear = False
					break
			if DoClear:
				target.clear(t, 1)
	def SetTagsInit(self, obj, target):
		"Set tags using each entry from a dictionary."
		for k, v in obj.items():
			if v == 1:
				self.SetTags(k, target)
