import wx
from pubsub import pub

ID_EMERGENCY_EXIT = wx.NewId()
ID_FILE_UPDATE_FORCE = wx.NewId()
ID_LEFT_IMAGE = wx.NewId()
ID_RIGHT_IMAGE = wx.NewId()
ID_LEFT_QUESTION = wx.NewId()
ID_RIGHT_QUESTION = wx.NewId()
ID_FOCUS_IMAGE_INDEX = wx.NewId()
ID_FOCUS_PATH_NAME = wx.NewId()
ID_FOCUS_QUESTION_INDEX = wx.NewId()
ID_FOCUS_PROMPT_BODY = wx.NewId()
ID_FOCUS_QUESTION_BODY = wx.NewId()
ID_IMAGE_QUALITY_LEFT = wx.NewId()
ID_IMAGE_QUALITY_RIGHT = wx.NewId()
ID_IMAGE_QUALITY_HIGH_2_1 = wx.NewId()
ID_IMAGE_QUALITY_HIGH_2 = wx.NewId()
ID_IMAGE_QUALITY_HIGH_1 = wx.NewId()
ID_IMAGE_QUALITY_MEDIUM = wx.NewId()
ID_IMAGE_QUALITY_LOW = wx.NewId()
ID_PAN_LEFT = wx.NewId()
ID_PAN_RIGHT = wx.NewId()
ID_PAN_UP = wx.NewId()
ID_PAN_DOWN = wx.NewId()
ID_ZOOM_IN = wx.NewId()
ID_ZOOM_OUT = wx.NewId()
ID_ZOOM_FIT = wx.NewId()
ID_ZOOM_ACTUAL_SIZE = wx.NewId()
KEYBIND_IDS = {
	'exit'                   : ID_EMERGENCY_EXIT        ,
	'flush_changes'          : ID_FILE_UPDATE_FORCE     ,
	'left_image'             : ID_LEFT_IMAGE            ,
	'right_image'            : ID_RIGHT_IMAGE           ,
	'left_question'          : ID_LEFT_QUESTION         ,
	'right_question'         : ID_RIGHT_QUESTION        ,
	'select_image_index'     : ID_FOCUS_IMAGE_INDEX     ,
	'select_image_path'      : ID_FOCUS_PATH_NAME       ,
	'select_question_index'  : ID_FOCUS_QUESTION_INDEX  ,
	'select_instructions'    : ID_FOCUS_PROMPT_BODY     ,
	'select_question'        : ID_FOCUS_QUESTION_BODY   ,
	'image_quality_left'     : ID_IMAGE_QUALITY_LEFT    ,
	'image_quality_right'    : ID_IMAGE_QUALITY_RIGHT   ,
	'image_quality_high_2_1' : ID_IMAGE_QUALITY_HIGH_2_1,
	'image_quality_high_2'   : ID_IMAGE_QUALITY_HIGH_2  ,
	'image_quality_high_1'   : ID_IMAGE_QUALITY_HIGH_1  ,
	'image_quality_medium'   : ID_IMAGE_QUALITY_MEDIUM  ,
	'image_quality_low'      : ID_IMAGE_QUALITY_LOW     ,
	'pan_left'               : ID_PAN_LEFT              ,
	'pan_right'              : ID_PAN_RIGHT             ,
	'pan_up'                 : ID_PAN_UP                ,
	'pan_down'               : ID_PAN_DOWN              ,
	'zoom_in'                : ID_ZOOM_IN               ,
	'zoom_out'               : ID_ZOOM_OUT              ,
	'zoom_fit'               : ID_ZOOM_FIT              ,
	'zoom_actual_size'       : ID_ZOOM_ACTUAL_SIZE
}
KEYBIND_MESSAGES = {
	ID_EMERGENCY_EXIT         : 'EmergencyExit'      ,
	ID_FILE_UPDATE_FORCE      : 'FileUpdateForce'    ,
	ID_LEFT_IMAGE             : 'LeftImage'          ,
	ID_RIGHT_IMAGE            : 'RightImage'         ,
	ID_LEFT_QUESTION          : 'LeftQuestion'       ,
	ID_RIGHT_QUESTION         : 'RightQuestion'      ,
	ID_FOCUS_IMAGE_INDEX      : 'FocusImageIndex'    ,
	ID_FOCUS_PATH_NAME        : 'FocusPathName'      ,
	ID_FOCUS_QUESTION_INDEX   : 'FocusQuestionIndex' ,
	ID_FOCUS_PROMPT_BODY      : 'FocusPromptBody'    ,
	ID_FOCUS_QUESTION_BODY    : 'FocusQuestionBody'  ,
	ID_IMAGE_QUALITY_LEFT     : 'ImageQualityLeft'   ,
	ID_IMAGE_QUALITY_RIGHT    : 'ImageQualityRight'  ,
	ID_IMAGE_QUALITY_HIGH_2_1 : 'ImageQualityHigh21' ,
	ID_IMAGE_QUALITY_HIGH_2   : 'ImageQualityHigh2'  ,
	ID_IMAGE_QUALITY_HIGH_1   : 'ImageQualityHigh1'  ,
	ID_IMAGE_QUALITY_MEDIUM   : 'ImageQualityMedium' ,
	ID_IMAGE_QUALITY_LOW      : 'ImageQualityLow'    ,
	ID_PAN_LEFT               : 'PanLeft'            ,
	ID_PAN_RIGHT              : 'PanRight'           ,
	ID_PAN_UP                 : 'PanUp'              ,
	ID_PAN_DOWN               : 'PanDown'            ,
	ID_ZOOM_IN                : 'ZoomIn'             ,
	ID_ZOOM_OUT               : 'ZoomOut'            ,
	ID_ZOOM_FIT               : 'ZoomFit'            ,
	ID_ZOOM_ACTUAL_SIZE       : 'ZoomActualSize'
}

class KeyHandlerError(Exception):
	pass

class KeyHandler(wx.Object):
	def __init__(self):
		self.EmergencyExitItem = wx.MenuItem(id=wx.NewId(), text="EmergencyExit", helpString="Exit the application.")
		self.FileUpdateForceItem = wx.MenuItem(id=wx.NewId(), text="FileUpdateForce", helpString="Flush output files to hard drive, if changed.")
		self.LeftImageItem = wx.MenuItem(id=wx.NewId(), text="LeftImage", helpString="Switch to the 'left' or previous image.")
		self.RightImageItem = wx.MenuItem(id=wx.NewId(), text="RightImage", helpString="Switch to the 'right' or next image.")
		self.LeftQuestionItem = wx.MenuItem(id=wx.NewId(), text="LeftQuestion", helpString="Switch to the 'left' or previous image.")
		self.RightQuestionItem = wx.MenuItem(id=wx.NewId(), text="RightQuestion", helpString="Switch to the 'right' or next image.")
		self.FocusImageIndexItem = wx.MenuItem(id=wx.NewId(), text="FocusImageIndex", helpString="Focus on the image index entry.")
		self.FocusImagePathItem = wx.MenuItem(id=wx.NewId(), text="FocusPathName", helpString="Focus on the image path name.")
		self.FocusQuestionIndexItem = wx.MenuItem(id=wx.NewId(), text="FocusQuestionIndex", helpString="Focus on the question index entry.")
		self.FocusInstructionsItem = wx.MenuItem(id=wx.NewId(), text="FocusPromptBody", helpString="Focus on the prompt text.")
		self.FocusQuestionsItem = wx.MenuItem(id=wx.NewId(), text="FocusQuestionBody", helpString="Focus on the question field.")
		self.ImageQualityLeftItem = wx.MenuItem(id=wx.NewId(), text="ImageQualityLeft", helpString="Cycle through image quality from low to high.")
		self.ImageQualityRightItem = wx.MenuItem(id=wx.NewId(), text="ImageQualityRight", helpString="Cycle through image quality from high to low.")
		self.ImageQualityHigh21Item = wx.MenuItem(id=wx.NewId(), text="ImageQualityHigh21", helpString="Set image quality to high (box average on downscale, bicubic on upscale).")
		self.ImageQualityHigh2Item = wx.MenuItem(id=wx.NewId(), text="ImageQualityHigh2", helpString="Set image quality to high (bicubic).")
		self.ImageQualityHigh1Item = wx.MenuItem(id=wx.NewId(), text="ImageQualityHigh1", helpString="Set image quality to high (box average).")
		self.ImageQualityMediumItem = wx.MenuItem(id=wx.NewId(), text="ImageQualityMedium", helpString="Set image quality to medium.")
		self.ImageQualityLowItem = wx.MenuItem(id=wx.NewId(), text="ImageQualityLow", helpString="Set image quality to low.")
		self.PanLeftItem = wx.MenuItem(id=wx.NewId(), text="PanLeft", helpString="Pan image left.")
		self.PanRightItem = wx.MenuItem(id=wx.NewId(), text="PanRight", helpString="Pan image right.")
		self.PanUpItem = wx.MenuItem(id=wx.NewId(), text="PanUp", helpString="Pan image up.")
		self.PanDownItem = wx.MenuItem(id=wx.NewId(), text="PanDown", helpString="Pan image down.")
		self.ZoomInItem = wx.MenuItem(id=wx.NewId(), text="ZoomIn", helpString="Zoom in image.")
		self.ZoomOutItem = wx.MenuItem(id=wx.NewId(), text="ZoomOut", helpString="Zoom out image.")
		self.ZoomFitItem = wx.MenuItem(id=wx.NewId(), text="ZoomFit", helpString="Zoom image to fit perfectly in the window.")
		self.ZoomActualSizeItem = wx.MenuItem(id=wx.NewId(), text="ZoomActualSize", helpString="Zoom image so it is displayed at actual size, whether or not it fits in the window.")
		self.MenuItems = {'exit'                   : self.EmergencyExitItem      ,
						  'flush_changes'          : self.FileUpdateForceItem    ,
						  'left_image'             : self.LeftImageItem          ,
						  'right_image'            : self.RightImageItem         ,
						  'left_question'          : self.LeftQuestionItem       ,
						  'right_question'         : self.RightQuestionItem      ,
						  'select_image_index'     : self.FocusImageIndexItem    ,
						  'select_image_path'      : self.FocusImagePathItem     ,
						  'select_question_index'  : self.FocusQuestionIndexItem ,
						  'select_instructions'    : self.FocusInstructionsItem  ,
						  'select_question'        : self.FocusQuestionsItem     ,
						  'image_quality_left'     : self.ImageQualityLeftItem   ,
						  'image_quality_right'    : self.ImageQualityRightItem  ,
						  'image_quality_high_2_1' : self.ImageQualityHigh21Item ,
						  'image_quality_high_2'   : self.ImageQualityHigh2Item  ,
						  'image_quality_high_1'   : self.ImageQualityHigh1Item  ,
						  'image_quality_medium'   : self.ImageQualityMediumItem ,
						  'image_quality_low'      : self.ImageQualityLowItem    ,
						  'pan_left'               : self.PanLeftItem            ,
						  'pan_right'              : self.PanRightItem           ,
						  'pan_up'                 : self.PanUpItem              ,
						  'pan_down'               : self.PanDownItem            ,
						  'zoom_in'                : self.ZoomInItem             ,
						  'zoom_out'               : self.ZoomOutItem            ,
						  'zoom_fit'               : self.ZoomFitItem            ,
						  'zoom_actual_size'       : self.ZoomActualSizeItem
						 }
		self.entries = []
	def _OnEntry(self, e):
		pub.sendMessage(KEYBIND_MESSAGES[e.GetId()], message = None)
	def RegisterObj(self, obj):
		obj.SetAcceleratorTable( wx.AcceleratorTable(self.entries) )

		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_EMERGENCY_EXIT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FILE_UPDATE_FORCE)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_LEFT_IMAGE)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_RIGHT_IMAGE)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_LEFT_QUESTION)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_RIGHT_QUESTION)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_IMAGE_INDEX)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_PATH_NAME)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_QUESTION_INDEX)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_PROMPT_BODY)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_FOCUS_QUESTION_BODY)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_LEFT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_RIGHT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_HIGH_2_1)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_HIGH_2)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_HIGH_1)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_MEDIUM)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_IMAGE_QUALITY_LOW)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_PAN_LEFT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_PAN_RIGHT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_PAN_UP)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_PAN_DOWN)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_ZOOM_IN)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_ZOOM_OUT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_ZOOM_FIT)
		obj.Bind(wx.EVT_MENU, self._OnEntry, id=ID_ZOOM_ACTUAL_SIZE)
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
