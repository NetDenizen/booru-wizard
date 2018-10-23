import wx
from pubsub import pub

ID_EMERGENCY_EXIT = wx.NewId()
ID_LEFT_IMAGE = wx.NewId()
ID_RIGHT_IMAGE = wx.NewId()
ID_LEFT_QUESTION = wx.NewId()
ID_RIGHT_QUESTION = wx.NewId()
ID_FOCUS_IMAGE_INDEX = wx.NewId()
ID_FOCUS_PATH_LABEL = wx.NewId()
ID_FOCUS_QUESTION_INDEX = wx.NewId()
ID_FOCUS_PROMPT_BODY = wx.NewId()
ID_FOCUS_QUESTION_BODY = wx.NewId()
KEYBIND_IDS = {
	'exit'                  : ID_EMERGENCY_EXIT      ,
	'left_image'            : ID_LEFT_IMAGE          ,
	'right_image'           : ID_RIGHT_IMAGE         ,
	'left_question'         : ID_LEFT_QUESTION       ,
	'right_question'        : ID_RIGHT_QUESTION      ,
	'select_image_index'    : ID_FOCUS_IMAGE_INDEX   ,
	'select_image_path'     : ID_FOCUS_PATH_LABEL    ,
	'select_question_index' : ID_FOCUS_QUESTION_INDEX,
	'select_instructions'   : ID_FOCUS_PROMPT_BODY   ,
	'select_question'       : ID_FOCUS_QUESTION_BODY ,
}
KEYBIND_MESSAGES = {
	ID_EMERGENCY_EXIT       : 'EmergencyExit'     ,
	ID_LEFT_IMAGE           : 'LeftImage'         ,
	ID_RIGHT_IMAGE          : 'RightImage'        ,
	ID_LEFT_QUESTION        : 'LeftQuestion'      ,
	ID_RIGHT_QUESTION       : 'RightQuestion'     ,
	ID_FOCUS_IMAGE_INDEX    : 'FocusImageIndex'   ,
	ID_FOCUS_PATH_LABEL     : 'FocusPathLabel'    ,
	ID_FOCUS_QUESTION_INDEX : 'FocusQuestionIndex',
	ID_FOCUS_PROMPT_BODY    : 'FocusPromptBody'   ,
	ID_FOCUS_QUESTION_BODY  : 'FocusQuestionBody' ,
}

class KeyHandlerError(Exception):
	pass

class KeyHandler(wx.Object):
	def __init__(self):
		self.EmergencyExitItem = wx.MenuItem(id=wx.NewId(), text="EmergencyExit", helpString="Exit the application.")
		self.LeftImageItem = wx.MenuItem(id=wx.NewId(), text="LeftImage", helpString="Switch to the 'left' or previous image.")
		self.RightImageItem = wx.MenuItem(id=wx.NewId(), text="RightImage", helpString="Switch to the 'right' or next image.")
		self.LeftQuestionItem = wx.MenuItem(id=wx.NewId(), text="LeftQuestion", helpString="Switch to the 'left' or previous image.")
		self.RightQuestionItem = wx.MenuItem(id=wx.NewId(), text="RightQuestion", helpString="Switch to the 'right' or next image.")
		self.FocusImageIndexItem = wx.MenuItem(id=wx.NewId(), text="FocusImageIndex", helpString="Focus on the image index entry.")
		self.FocusImagePathItem = wx.MenuItem(id=wx.NewId(), text="FocusPathLabel", helpString="Focus on the image path label.")
		self.FocusQuestionIndexItem = wx.MenuItem(id=wx.NewId(), text="FocusQuestionIndex", helpString="Focus on the question index entry.")
		self.FocusInstructionsItem = wx.MenuItem(id=wx.NewId(), text="FocusPromptBody", helpString="Focus on the prompt text.")
		self.FocusQuestionsItem = wx.MenuItem(id=wx.NewId(), text="FocusQuestionBody", helpString="Focus on the question field.")
		self.MenuItems = {'exit'                  : self.EmergencyExitItem     ,
						  'left_image'            : self.LeftImageItem         ,
						  'right_image'           : self.RightImageItem        ,
						  'left_question'         : self.LeftQuestionItem      ,
						  'right_question'        : self.RightQuestionItem     ,
						  'select_image_index'    : self.FocusImageIndexItem   ,
						  'select_image_path'     : self.FocusImagePathItem    ,
						  'select_question_index' : self.FocusQuestionIndexItem,
						  'select_instructions'   : self.FocusInstructionsItem ,
						  'select_question'       : self.FocusQuestionsItem    ,
						 }
		self.entries = []
	def _OnEntry(self, e):
			pub.sendMessage(KEYBIND_MESSAGES[e.GetId()], message = None)
	def RegisterObj(self, obj):
		obj.SetAcceleratorTable( wx.AcceleratorTable(self.entries) )

		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_EMERGENCY_EXIT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_LEFT_IMAGE)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_RIGHT_IMAGE)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_LEFT_QUESTION)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_RIGHT_QUESTION)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_IMAGE_INDEX)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_PATH_LABEL)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_QUESTION_INDEX)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_PROMPT_BODY)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_QUESTION_BODY)
	def add(self, text):
		"Add a keybind to the handler."
		values = text.split()
		if not values:
			raise KeyHandlerError("Empty keybind specified.")
		if len(values) != 2:
			raise KeyHandlerError("Keybind must follow format: <name><whitespace><bind>.")
		KeybindID = KEYBIND_IDS.get( values[0].lower(), None )
		if KeybindID is None:
			raise KeyHandlerError( ''.join( ('Keybind name "', values[0].lower(), '" is invalid.') ) )
		# TODO: Can we find a less circuitous way to do this?
		DummyEntry = wx.AcceleratorEntry()
		success = DummyEntry.FromString(values[1])
		if not success:
			raise KeyHandlerError( ''.join( ('Keybind "', values[1], '" is invalid.') ) )
		entry = wx.AcceleratorEntry()
		entry.Set(DummyEntry.GetFlags(), DummyEntry.GetKeyCode(),
				  KEYBIND_IDS[values[0].lower()], self.MenuItems[values[0].lower()])
		self.entries.append(entry)
	def AddList(self, values):
		for v in values:
			self.add(v)
