import re
from enum import Enum
import colorsys

from booruwizard.lib.fileops import SAFETY_NAMES_LOOKUP, DEFAULT_SAFETY, DEFAULT_MAX_OPEN_FILES, DEFAULT_UPDATE_INTERVAL, DEFAULT_MAX_IMAGE_BUFSIZE, DEFAULT_IMAGE_QUALITY, IMAGE_QUALITY_LOOKUP
from booruwizard.lib.tag import TagsContainer, ConditionalTagger
from booruwizard.lib.alphabackground import DEFAULT_COLOR1_PIXEL, DEFAULT_COLOR2_PIXEL, DEFAULT_SQUARE_WIDTH

# Generic template error definition
class TemplateError(Exception):
	def __init__(self, message, line, col):
		super().__init__( ''.join( ( message, ' Line: ', str(line), ' Col: ', str(col) ) ) )

# Key-value pair definition
class PairKey(Enum):
	RADIO_QUESTION                = 0
	CHECK_QUESTION                = 1
	OPTION_NAME                   = 2
	OPTION_TAG                    = 3
	ENTRY_QUESTION                = 4
	SESSION_TAGS                  = 5
	NAME_QUESTION                 = 6
	SOURCE_QUESTION               = 7
	DEFAULT_SOURCE                = 8
	NAMELESS_TAG                  = 9
	SOURCELESS_TAG                = 10
	TAGLESS_TAG                   = 11
	SAFETY_QUESTION               = 12
	DEFAULT_SAFETY                = 13
	MAX_OPEN_FILES                = 14
	UPDATE_INTERVAL               = 15
	MAX_IMAGE_BUFSIZE             = 16
	ALIAS_TAG_TO                  = 17
	ALIAS_TAG_FROM                = 18
	IMAGE_BACKGROUND_COLOR_ONE    = 19
	IMAGE_BACKGROUND_COLOR_TWO    = 20
	IMAGE_BACKGROUND_SQUARE_WIDTH = 21
	KEYBIND                       = 22
	IMAGE_TAGS_ENTRY              = 23
	DEFAULT_IMAGE_QUALITY         = 24
	#TODO: Should MAX_OPEN_FILES and UPDATE_INTERVAL be editable during program operation?
	#TODO: keyboard controls, alias name and alias tag separately, no option tag

PAIR_KEY_NAMES = {
	'RADIO_QUESTION'                : PairKey.RADIO_QUESTION,
	'CHECK_QUESTION'                : PairKey.CHECK_QUESTION,
	'OPTION_NAME'                   : PairKey.OPTION_NAME,
	'OPTION_TAG'                    : PairKey.OPTION_TAG,
	'ENTRY_QUESTION'                : PairKey.ENTRY_QUESTION,
	'SESSION_TAGS'                  : PairKey.SESSION_TAGS,
	'NAME_QUESTION'                 : PairKey.NAME_QUESTION,
	'SOURCE_QUESTION'               : PairKey.SOURCE_QUESTION,
	'DEFAULT_SOURCE'                : PairKey.DEFAULT_SOURCE,
	'NAMELESS_TAG'                  : PairKey.NAMELESS_TAG,
	'SOURCELESS_TAG'                : PairKey.SOURCELESS_TAG,
	'TAGLESS_TAG'                   : PairKey.TAGLESS_TAG,
	'SAFETY_QUESTION'               : PairKey.SAFETY_QUESTION,
	'DEFAULT_SAFETY'                : PairKey.DEFAULT_SAFETY,
	'MAX_OPEN_FILES'                : PairKey.MAX_OPEN_FILES,
	'UPDATE_INTERVAL'               : PairKey.UPDATE_INTERVAL,
	'MAX_IMAGE_BUFSIZE'             : PairKey.MAX_IMAGE_BUFSIZE,
	'ALIAS_TAG_TO'                  : PairKey.ALIAS_TAG_TO,
	'ALIAS_TAG_FROM'                : PairKey.ALIAS_TAG_FROM,
	'IMAGE_BACKGROUND_COLOR_ONE'    : PairKey.IMAGE_BACKGROUND_COLOR_ONE,
	'IMAGE_BACKGROUND_COLOR_TWO'    : PairKey.IMAGE_BACKGROUND_COLOR_TWO,
	'IMAGE_BACKGROUND_SQUARE_WIDTH' : PairKey.IMAGE_BACKGROUND_SQUARE_WIDTH,
	'KEYBIND'                       : PairKey.KEYBIND,
	'IMAGE_TAGS_ENTRY'              : PairKey.IMAGE_TAGS_ENTRY,
	'DEFAULT_IMAGE_QUALITY'         : PairKey.DEFAULT_IMAGE_QUALITY
}

class KeyValuePair:
	def __init__(self, line, col, key, value):
		self.line = line
		self.col = col
		self.key = key # PairKey enum value.
		self.value = value # String.

# Lexer definition
class LexerError(TemplateError):
	pass

RE_NEWLINE_SINGLE = re.compile('[\n\r]')
RE_NEWLINE        = re.compile('[\n\r]+')
RE_NOT_WHITESPACE = re.compile(r'\S')
RE_KEY_END        = re.compile(r'[\s:]')
RE_QUOTE          = re.compile(r'(?<!\\)"')

class lexer:
	def __init__(self):
		# Input and offset in it.
		self._input = ""
		self._pos = 0

		# Logical in input; used for error messages.
		self._LineStart = 0
		self._line = 0
		self._col = 0

		# Output array of key-value pair objects.
		self.output = []
	def _search(self, regex):
		"Search for a specific regex from the current position in input. If it can be found, then advance the position to the beginning of that expression and return its length. If not, then return 0."
		m = regex.search(self._input[self._pos:])
		if m is not None:
			self._pos += m.start(0)
			return len( m.group(0) )
		else:
			return 0
	def _TrackLinePos(self, StartPos, EndPos):
		"Count the number of newlines between StartPos and EndPos, and update position accordingly."
		if StartPos == EndPos:
			return
		pos = StartPos
		m = RE_NEWLINE_SINGLE.search(self._input[pos:EndPos])
		while m is not None:
			pos += ( m.start(0) + len( m.group(0) ) )
			self._LineStart = pos
			self._line += 1
			m = RE_NEWLINE_SINGLE.search(self._input[pos:EndPos])
		self._col = EndPos - self._LineStart
	def _ParseComment(self):
		"Search until beginning of next line."
		#TODO: We cannot directly add the return value of _search
		StartPos = self._pos
		tmp = self._search(RE_NEWLINE)
		self._pos += tmp
		self._TrackLinePos(StartPos, self._pos)
	def _ParseWhitespace(self):
		"Search until not in whitespace."
		StartPos = self._pos
		self._search(RE_NOT_WHITESPACE)
		self._TrackLinePos(StartPos, self._pos)
	def _ParseKey(self):
		"Parse entire key up to the ':'."
		KeyStart = self._pos
		KeyStartLine = self._line
		KeyStartCol = self._col
		self._search(RE_KEY_END)
		self._TrackLinePos(KeyStart, self._pos)
		KeyName = self._input[KeyStart:self._pos]
		KeyEnum = PAIR_KEY_NAMES.get(KeyName, None)
		if KeyEnum is None:
			raise LexerError( ''.join( ("Key '", KeyName, "' is invalid") ), KeyStartLine, KeyStartCol )
		self._ParseWhitespace()
		if self._input[self._pos] != ':':
			raise LexerError("Key found without terminating ':'", self._line, self._col)
		self._pos += 1
		self._col += 1
		return KeyEnum
	def _ParseVal(self):
		"Parse entire value, including the closing '\"'."
		self._ParseWhitespace()
		if self._input[self._pos] != '"':
			raise LexerError("Value without opening '\"'", self._line, self._col)
		self._pos += 1
		self._col += 1
		ValStart = self._pos
		self._search(RE_QUOTE)
		self._TrackLinePos(ValStart, self._pos)
		if self._input[self._pos] != '"':
			raise LexerError("Value without closing '\"'", self._line, self._col)
		val = self._input[ValStart:self._pos]
		self._pos += 1
		self._col += 1
		return val.replace('\\"', '"')
	def _ParsePair(self):
		"Parse an entire key pair, to add it to the output array."
		line = self._line
		col = self._col
		key = self._ParseKey()
		val = self._ParseVal()
		self.output.append( KeyValuePair(line, col, key, val) )
	def _GetNextPair(self):
		"Progress to next key pair in file, then parse it."
		while True:
			self._ParseWhitespace()
			if self._pos >= len(self._input) - 1:
				return
			c = self._input[self._pos]
			if c == '#':
				self._ParseComment()
			else:
				break
		self._ParsePair()
	def parse(self, string):
		"Parse the input string and leave the result in the output array."
		self._input = string
		while self._pos < len( self._input ) - 1:
			self._GetNextPair()

# Defining parser question information
class QuestionType(Enum):
	ENTRY_QUESTION   = 0 # Marks the beginning of a new prompt consisting of a textbox. Here, tags are entered separated by spaces.
	SESSION_TAGS     = 1 # Displays a CHECK_QUESTION, containing all of the tags used for the current session.
	NAME_QUESTION    = 2 # Displays an ENTRY_QUESTION that sets the name/title of the post. In most boorus other than Gelbooru 0.1, this is ignored.
	SOURCE_QUESTION  = 3 # Displays an ENTRY_QUESTION that sets the original source of the work.
	SAFETY_QUESTION  = 4 # Displays a RADIO_QUESTION that sets the content rating to 'Safe', 'Questionable', or 'Explicit'.
	IMAGE_TAGS_ENTRY = 5 # Displays an ENTRY_QUESTION with the current tags of the image.

QuestionTypeLookup = {
	PairKey.ENTRY_QUESTION  : QuestionType.ENTRY_QUESTION,
	PairKey.SESSION_TAGS    : QuestionType.SESSION_TAGS,
	PairKey.NAME_QUESTION   : QuestionType.NAME_QUESTION,
	PairKey.SOURCE_QUESTION : QuestionType.SOURCE_QUESTION,
	PairKey.SAFETY_QUESTION : QuestionType.SAFETY_QUESTION,
	PairKey.IMAGE_TAGS_ENTRY : QuestionType.IMAGE_TAGS_ENTRY,
}

class OptionQuestionType(Enum):
	RADIO_QUESTION = 0  # Marks the beginning of a new prompt consisting of radio buttons. This allows only ONE tag to be chosen.
	CHECK_QUESTION = 1  # Marks the beginning of a new prompt consisting of check boxes. This allows any number of tags to be chosen.

OptionQuestionTypeLookup = {
	PairKey.RADIO_QUESTION : OptionQuestionType.RADIO_QUESTION,
	PairKey.CHECK_QUESTION : OptionQuestionType.CHECK_QUESTION
}

class question:
	def __init__(self, ThisType, text):
		self.type = ThisType
		self.text = text

class option:
	def __init__(self, name, tag):
		self.name = name
		self.tag = tag

class OptionQuestion(question):
	def __init__(self, ThisType, text):
		super().__init__(ThisType, text)
		self.options = []
	def GetChoiceNames(self):
		output = []
		for o in self.options:
			output.append(o.name)
		return output
	def GetChoiceTags(self):
		output = []
		for o in self.options:
			output.append(o.tag)
		return output

# Defining the color container class
class ColorError(TemplateError):
	pass

class color:
	def _ParseHexTriplet(self, text, line, col):
		if len(text) != 7:
			raise ColorError("Value should follow format '#XXXXXX'; exactly 7 characters, with arbitrary whitespace before and after.", line, col)
		try:
			self.red = float( int(text[1:3], 16) ) / 255.0
			self.green = float( int(text[3:5], 16) ) / 255.0
			self.blue = float( int(text[5:7], 16) ) / 255.0
		except ValueError as err:
			raise ColorError(err, line, col)
	def _CopyColor(self, a, b, c):
		"Copy the three arguments to a tuple, and return it."
		return (a, b, c)
	def _ParseParamQuad(self, text, line, col):
		inputs = text.split()
		if len(inputs) != 4:
			raise ColorError("Value should follow format: '<name> <value 1> <value 2> <value 3>'.", line, col)
		values = [0] * 3
		if inputs[0] == 'rgb':
			dividers = [255.0, 255.0, 255.0]
			names = ['red', 'green', 'blue']
			conv = self._CopyColor
		elif inputs[0] == 'hsv':
			dividers = [360.0, 100.0, 100.0]
			names = ['hue', 'saturation', 'value']
			conv = colorsys.hsv_to_rgb
		elif inputs[0] == 'hls':
			dividers = [360.0, 100.0, 100.0]
			names = ['hue', 'lightness', 'saturation']
			conv = colorsys.hls_to_rgb
		else:
			raise ColorError(''.join( ("Color type must be 'rgb', 'hsv', or 'hls'. '", inputs[0], "' is not valid." ) ), line, col)
		i = 0
		for n, v, d in zip(names, inputs[1:], dividers):
			try:
				fv = float(v)
			except ValueError as err:
				raise ColorError(err, line, col)
			if fv > d:
				raise ColorError(''.join( ("Value ", str(i), " (", n, ") of '", v, "' must be less than '", str(d), "' and non-negative." ) ), line, col)
			elif fv < 0.0:
				raise ColorError(''.join( ("Value ", str(i), " (", n, ") of '", v, "' must be less than '", str(d), "' and non-negative." ) ), line, col)
			values[i] = float(v) / d
			i += 1
		self.red, self.green, self.blue = conv(values[0], values[1], values[2])
	def __init__(self, text, line, col):
		self.red = None
		self.green = None
		self.blue = None
		cleaned = text.strip().lower()
		if not cleaned:
			raise ColorError("Value is empty", line, col)
		if cleaned[0] == '#':
			self._ParseHexTriplet(cleaned, line, col)
		else:
			self._ParseParamQuad(cleaned, line, col)
	def ToBytearray(self):
		output = bytearray(3)
		output[0] = int(self.red * 255.0)
		output[1] = int(self.green * 255.0)
		output[2] = int(self.blue * 255.0)
		return output

# Main parser definition
class ParserError(TemplateError):
	pass

class ParserState(Enum):
	NORMAL          = 0 # The default parsing state.
	OPTION_QUESTION = 1 # When we are in a RADIO_QUESTION or CHECK_QUESTION which has options.
	OPTION_NAME     = 2 # When we added the name of an option and are waiting for the tag.
	ALIAS_FROM      = 3 # When we added the tags to alias from and are waiting for the tags to alias to.
	ALIAS_TO        = 4 # When we added the tags to alias to and are waiting for the tags to alias from.

RE_HUMANSIZE = re.compile('^([0-9\.]+)[ \t]*([a-zA-Z]*)$')
SIZE_SPECIFIERS = {'kB'       : 1000.0,
				   'kilobyte' : 1000.0,
				   'Kilobyte' : 1000.0,
				   'MB'       : 1000000.0,
				   'megabyte' : 1000000.0,
				   'Megabyte' : 1000000.0,
				   'GB'       : 1000000000.0,
				   'gigabyte' : 1000000000.0,
				   'Gigabyte' : 1000000000.0,
				   'KiB'      : 1024.0,
				   'kibibyte' : 1024.0,
				   'Kibibyte' : 1024.0,
				   'MiB'      : 1048576.0,
				   'mebibyte' : 1048576.0,
				   'Mebibyte' : 1048576.0,
				   'GiB'      : 1073741800.0,
				   'gibibyte' : 1073741800.0,
				   'Gibibyte' : 1073741800.0
}

class parser:
	def __init__(self):
		self._state = ParserState.NORMAL
		self._lexer = lexer()

		#TODO: Do this differently, like keep track of these strings in the conditional tagger?
		self._AliasFromString = ""
		self._AliasToString = ""

		self.DefaultName = None # Actually cannot currently be changed by the configuration file, but is here for extra flexibility.
		self.NamelessTags = TagsContainer()

		self.DefaultSource = None
		self.SourcelessTags = TagsContainer()

		self.ConditionalTags = ConditionalTagger()
		self.TaglessTags = TagsContainer()

		self.DefaultSafety = DEFAULT_SAFETY

		self.MaxOpenFiles = DEFAULT_MAX_OPEN_FILES
		self.UpdateInterval = DEFAULT_UPDATE_INTERVAL
		self.MaxImageBufSize = DEFAULT_MAX_IMAGE_BUFSIZE
		self.DefaultImageQuality = DEFAULT_IMAGE_QUALITY

		self.BackgroundColor1 = DEFAULT_COLOR1_PIXEL
		self.BackgroundColor2 = DEFAULT_COLOR2_PIXEL
		self.BackgroundSquareWidth = DEFAULT_SQUARE_WIDTH

		self.keybinds = []

		self.output = [] # Output array of question objects
	def _IsOptionQuestionPrepared(self):
		"Return True if the state is NORMAL or if the state is OPTION_QUESTION and there is at least one option entry in its array."
		if self._state == ParserState.NORMAL:
			return True
		if self._state == ParserState.OPTION_NAME or\
		   self._state == ParserState.ALIAS_FROM  or\
		   self._state == ParserState.ALIAS_TO:
			return False
		if not self.output[-1].options:
			return False
		else:
			return True
	def _AddQuestion(self, token):
		"Add a non-option question to the end of output"
		if not self._IsOptionQuestionPrepared():
			raise ParserError("New question started while existing question or alias is being defined.", token.line, token.col)
		self._state = ParserState.NORMAL
		self.output.append( question(QuestionTypeLookup[token.key], token.value) )
	def _AddOptionQuestion(self, token):
		"Add a option question to the end of output if possible and adjust the state accordingly."
		if not self._IsOptionQuestionPrepared():
			raise ParserError("New question started while existing question or alias is being defined.", token.line, token.col)
		self._state = ParserState.OPTION_QUESTION
		self.output.append( OptionQuestion(OptionQuestionTypeLookup[token.key], token.value) )
	def _AddOptionName(self, token):
		"Add an option name and adjust the state accordingly."
		if self._state == ParserState.OPTION_NAME:
			self.output[-1].options.append( option(token.value, "") )
		elif self._state == ParserState.OPTION_QUESTION:
			self.output[-1].options.append( option(token.value, "") )
			self._state = ParserState.OPTION_NAME
		else:
			raise ParserError("Option name added when not in a question.", token.line, token.col)
	def _AddOptionTag(self, token):
		if self._state == ParserState.OPTION_NAME:
			self.output[-1].options[-1].tag = token.value
			self._state = ParserState.OPTION_QUESTION
		elif self._state == ParserState.OPTION_QUESTION:
			self.output[-1].options.append( option(token.value, token.value) )
		else:
			raise ParserError("Option added when not in a question.", token.line, token.col)
	def _AddAliasTagFrom(self, token):
		if self._IsOptionQuestionPrepared:
			self._AliasFromString = token.value
			self._state = ParserState.ALIAS_FROM
		elif self._state == ParserState.ALIAS_FROM:
			self._AliasFromString = token.value
		elif self._state == ParserState.ALIAS_TO:
			self.ConditionalTags.AddString(token.value, self._AliasToString)
			self._AliasToString = ""
			self._state = ParserState.NORMAL
		else:
			raise ParserError("Alias source added when in a question.", token.line, token.col)
	def _AddAliasTagTo(self, token):
		if self._IsOptionQuestionPrepared():
			self._AliasToString = token.value
			self._state = ParserState.ALIAS_TO
		elif self._state == ParserState.ALIAS_FROM:
			self.ConditionalTags.AddString(self._AliasFromString, token.value)
			self._AliasFromString = ""
			self._state = ParserState.NORMAL
		elif self._state == ParserState.ALIAS_TO:
			self._AliasToString = token.value
		else:
			raise ParserError("Alias target added when in a question.", token.line, token.col)
	def _add(self, token):
		"Parse a single key-pair in the NORMAL state."
		#TODO: Convert this contional code to a lookup table?
		if token.key == PairKey.RADIO_QUESTION or\
		   token.key == PairKey.CHECK_QUESTION:
			self._AddOptionQuestion(token)
		elif token.key == PairKey.ENTRY_QUESTION  or\
			 token.key == PairKey.NAME_QUESTION   or\
			 token.key == PairKey.SOURCE_QUESTION or\
			 token.key == PairKey.SAFETY_QUESTION or\
			 token.key == PairKey.SESSION_TAGS    or\
			 token.key == PairKey.IMAGE_TAGS_ENTRY:
			self._AddQuestion(token)
		elif token.key == PairKey.OPTION_NAME:
			self._AddOptionName(token)
		elif token.key == PairKey.OPTION_TAG:
			if len( token.value.split() ) > 1: # TODO: Does this handle unicode spaces?
				raise ParserError( ''.join( ( 'Tag "', token.value, '" contains whitespace.' ) ), token.line, token.col )
			self._AddOptionTag(token)
		elif token.key == PairKey.DEFAULT_SOURCE:
			self.DefaultSource = token.value
		elif token.key == PairKey.NAMELESS_TAG:
			self.NamelessTags.SetString(token.value, 1)
		elif token.key == PairKey.SOURCELESS_TAG:
			self.SourcelessTags.SetString(token.value, 1)
		elif token.key == PairKey.TAGLESS_TAG:
			self.TaglessTags.SetString(token.value, 1)
		elif token.key == PairKey.DEFAULT_SAFETY:
			found = SAFETY_NAMES_LOOKUP.get(token.value, None)
			if found is None:
				raise ParserError(''.join( ("Invalid safety name '", token.value, "'") ), token.line, token.col)
			self.DefaultSafety = found
		elif token.key == PairKey.MAX_OPEN_FILES:
			try:
				self.MaxOpenFiles = int(token.value)
			except ValueError:
				raise ParserError(''.join( ("Failed to convert max open files '", token.value, "' to integer.") ), token.line, token.col)
		elif token.key == PairKey.UPDATE_INTERVAL:
			try:
				self.UpdateInterval = float(token.value)
			except ValueError:
				raise ParserError(''.join( ("Failed to convert update interval '", token.value, "' to integer.") ), token.line, token.col)
		elif token.key == PairKey.MAX_IMAGE_BUFSIZE:
			m = RE_HUMANSIZE.match(token.value)
			if m is None:
				raise ParserError(''.join( ("Unable to match size specified as: ", token.value) ), token.line, token.col)
			if m.group(2) != '':
				specifier = SIZE_SPECIFIERS.get(m.group(2), None)
				if specifier is None:
					raise ParserError(''.join( ( "Unable to look up size specifier: ", m.group(2) ) ), token.line, token.col)
			else:
				specifier = 1.0
			number = m.group(1)
			try:
				val = float(number)
			except ValueError as err:
				raise ParserError(''.join( ("Failed to convert number ", number, " to float: [", err, "]") ), token.line, token.col)
			self.MaxImageBufSize = int(val * specifier)
		elif token.key == PairKey.ALIAS_TAG_FROM:
			self._AddAliasTagFrom(token)
		elif token.key == PairKey.ALIAS_TAG_TO:
			self._AddAliasTagTo(token)
		elif token.key == PairKey.IMAGE_BACKGROUND_COLOR_ONE:
			self.BackgroundColor1 = color(token.value, token.line, token.col).ToBytearray()
		elif token.key == PairKey.IMAGE_BACKGROUND_COLOR_TWO:
			self.BackgroundColor2 = color(token.value, token.line, token.col).ToBytearray()
		elif token.key == PairKey.IMAGE_BACKGROUND_SQUARE_WIDTH:
			try:
				self.BackgroundSquareWidth = int(token.value)
			except ValueError:
				raise ParserError(''.join( ("Failed to convert background square width '", token.value, "' to integer.") ), token.line, token.col)
		elif token.key == PairKey.KEYBIND:
			self.keybinds.append(token.value)
		else: # token.key == PairKey.DEFAULT_IMAGE_QUALITY
			found = IMAGE_QUALITY_LOOKUP.get(token.value, None)
			if found is None:
				raise ParserError(''.join( ("Invalid image quality name '", token.value, "'") ), token.line, token.col)
			self.DefaultImageQuality = found
	def parse(self, string):
		"Parse the input string and leave the result in the output array."
		self._lexer.parse(string)
		for t in self._lexer.output:
			self._add(t)
