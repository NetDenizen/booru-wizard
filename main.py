import sys
import traceback
import os
import os.path
import argparse
import json
from collections import OrderedDict

import wx
from pubsub import pub
import jsonschema

from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import parser
from booruwizard.lib.fileops import FileManager
from booruwizard.lib.viewport import ViewPort
from booruwizard.lib.keyhandler import KeyHandler
from booruwizard.ui.main import FileDialogFrame, MainFrame

APPNAME = 'booru-wizard'
APPVERSION = '0.3'
APPTITLE = ''.join( ( APPNAME, ' (', APPVERSION, ')' ) )

#TODO: Better accept dialog?
class ExceptDialog(wx.Dialog):
	def _OnClose(self, e):
		pub.sendMessage("EmergencyExit", message = None)
		e.Skip()
	def __init__(self, msg):
		wx.Dialog.__init__( self, None, title=''.join( (APPTITLE, ' - Exception') ),
							style=wx.CAPTION | wx.SYSTEM_MENU | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX )
		text = wx.TextCtrl(self, value= msg, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_NOHIDESEL | wx.TE_AUTO_URL)
		text.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		self.Bind(wx.EVT_CLOSE, self._OnClose)

def ExceptHook(etype, value, trace):
	tmp = traceback.format_exception(etype, value, trace)
	exception = ''.join(tmp)

	wx.LogFatalError(exception)
	dialog = ExceptDialog(exception)
	dialog.ShowModal()
	dialog.Destroy()
sys.excepthook = ExceptHook

class MainError(Exception):
	pass

class DialogSettings:
	def __init__(self, SchemaFile, ConfigFile, ImageInputDir, JSONInputDir, JSONOutputDir):
		self.EarlyExit = True
		self.SchemaFile = SchemaFile
		self.ConfigFile = ConfigFile
		self.ImageInputDir = ImageInputDir
		self.JSONInputDir = JSONInputDir
		self.JSONOutputDir = JSONOutputDir
	def validate(self):
		if not os.path.exists(self.SchemaFile):
			raise MainError( ''.join( ('Schema file path: "', self.SchemaFile, '" does not exist.') ) )
		if not os.path.isfile(self.SchemaFile):
			raise MainError( ''.join( ('Schema file path: "', self.SchemaFile, '" is not a file.') ) )
		if not os.path.exists(self.ConfigFile):
			raise MainError( ''.join( ('Config file path: "', self.ConfigFile, '" does not exist.') ) )
		if not os.path.isfile(self.ConfigFile):
			raise MainError( ''.join( ('Config file path: "', self.ConfigFile, '" is not a file.') ) )
		if not os.path.exists(self.ImageInputDir):
			raise MainError( ''.join( ('Image file path: "', self.ImageInputDir, '" does not exist.') ) )
		if not os.path.isdir(self.ImageInputDir):
			raise MainError( ''.join( ('Image file path: "', self.ImageInputDir, '" is not a directory.') ) )
		if not os.path.exists(self.JSONInputDir):
			raise MainError( ''.join( ('JSON input file path: "', self.JSONInputDir, '" does not exist.') ) )
		if not os.path.isdir(self.JSONInputDir):
			raise MainError( ''.join( ('JSON input file path: "', self.JSONInputDir, '" is not a directory.') ) )
		if not os.path.exists(self.JSONOutputDir):
			raise MainError( ''.join( ('JSON output file path: "', self.JSONOutputDir, '" does not exist.') ) )
		if not os.path.isdir(self.JSONOutputDir):
			raise MainError( ''.join( ('JSON output file path: "', self.JSONOutputDir, '" is not a directory.') ) )

def ParseCommandLine():
	"Function to create a command line argument parser, and return the args object from it."
	ArgParser = argparse.ArgumentParser(description='Get command line arguments.')
	ArgParser.add_argument( '--verbose', '-v', action='store_true', help='If this is set, then the program will produce verbose logging output.' )
	ArgParser.add_argument( '--no-dialog', '-d', action='store_true', help='If this is set, then the file chooser dialog will not be displayed before the regular UI. Thus, the command line settings are relied upon.' )
	ArgParser.add_argument( '--schema', '-s', action='store', default='', help='Path to read schema file from.' )
	ArgParser.add_argument( '--config', '-c', action='store', default='', help='Path to read config file from.' )
	ArgParser.add_argument( '--image-input', '-i', action='store', default='', help='Path to the image input directory.' )
	ArgParser.add_argument( '--json-input', '-j', action='store', default='', help='Path to the JSON input directory. If none, then it will be copied from "--image-input".' )
	ArgParser.add_argument( '--json-output', '-o', action='store', default='', help='Path to the JSON output directory. If none, then copy it will be copied from "--json-input".' )
	return ArgParser.parse_args()

def ReadTextFile(path):
	"Function to open a text file, and return the string from its contents."
	contents = None
	try:
		File = open( path, 'r' )
	except OSError as err:
		raise MainError( ''.join( ('Failed to open file at path: ', path, ' [errno ', err.errno, ']: ', err.strerror) ) )
	contents = File.read()
	File.close()
	return contents

def ParseJSONFile(path):
	"Function to parse a JSON file to a Python object, and return it."
	obj = None
	contents = ReadTextFile(path)
	try:
		obj = json.loads(contents, object_pairs_hook=OrderedDict)
	except json.decoder.JSONDecodeError as err:
		raise MainError( ''.join( ('Failed to decode JSON file at path: "', path, '" Reason: "', err.msg, '" Line: ', str(err.lineno), ' Col: ', str(err.colno) ) ) )
	return obj

def VerifyJSONSchema(path, obj, schema):
	"Function to validate a JSON object against a schema."
	try:
		jsonschema.validate(obj, schema)
	except jsonschema.ValidationError as err:
		raise MainError( ''.join( ('Failed to validate JSON file at path: "', path, '" ', err.message) ) )

def GetDirFiles(DirPath):
	"Function to get all file paths from a directory."
	try:
		output = []
		for n in sorted( os.listdir(DirPath) ):
			f = os.path.join(DirPath, n)
			if os.path.isfile(f):
				output.append(f)
		return output
	except OSError as err:
		raise MainError( ''.join( ('Failed to get files from directory at: ', DirPath, ' [errno ', err.errno, ']: ', err.strerror) ) )

VALID_IMAGES = ('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.jpe', '.jif', '.jfif', '.jfi', '.gif', '.pcx', '.pbm', '.pgm', '.ppm', '.pnm', '.tiff', '.tif', '.tga', '.icb', '.vda', '.vst', '.iff', '.xpm', '.ico', '.cur', '.ani')
VALID_JSON = ('.json',)
def GetFileTypes(paths, images):
	"Function to get those paths which are for images from a list, and return them."
	output = []
	for p in paths:
		if os.path.splitext(p)[1].lower() in images:
			output.append(p)
	return output

def main():
	"Main procedure."

	app = wx.App()
	wx.Log.SetActiveTarget( wx.LogStderr() )
	args = ParseCommandLine()
	if args.verbose:
		wx.Log.SetVerbose()

	settings = DialogSettings(args.schema, args.config, args.image_input, args.json_input, args.json_output)
	if not args.no_dialog:
		dialog = FileDialogFrame(None, APPTITLE, settings)
		dialog.Show()
		app.MainLoop()
		if settings.EarlyExit:
			sys.exit(0)
	if not settings.JSONInputDir:
		settings.JSONInputDir = settings.ImageInputDir
	if not settings.JSONOutputDir:
		settings.JSONOutputDir = settings.JSONInputDir
	settings.validate()

	schema = ParseJSONFile(settings.SchemaFile)
	ImagePaths = GetFileTypes(GetDirFiles(settings.ImageInputDir), VALID_IMAGES)
	JSONPaths = GetFileTypes(GetDirFiles(settings.JSONInputDir), VALID_JSON)

	config = parser()
	config.parse( ReadTextFile(settings.ConfigFile) )

	viewport = ViewPort(config.BackgroundColor1, config.BackgroundColor2, config.BackgroundSquareWidth,
						config.StartZoomInterval, config.ZoomAccel, config.ZoomAccelSteps, config.PanInterval)

	OutputFiles = FileManager(config.MaxOpenFiles, config.UpdateInterval)
	OutputFiles.FilesLock.acquire()
	for p in ImagePaths:
		OutputFiles.AddFile(settings.ImageInputDir, settings.JSONOutputDir, p,
							config.DefaultName, config.DefaultSource, config.DefaultSafety,
							config.ConditionalTags, config.NamelessTags, config.SourcelessTags, config.TaglessTags)
	for p in JSONPaths:
		obj = ParseJSONFile( os.path.join(settings.JSONInputDir, p) )
		VerifyJSONSchema(p, obj, schema)
		OutputFiles.AddJSON(settings.ImageInputDir, settings.JSONOutputDir, obj,
							config.DefaultName, config.DefaultSource, config.DefaultSafety,
							config.ConditionalTags, config.NamelessTags, config.SourcelessTags, config.TaglessTags)

	if not OutputFiles.ControlFiles:
		raise MainError('No input files found.')

	TagsTracker = TagsContainer()
	for f in OutputFiles.ControlFiles:
		TagsTracker.AddStringList( f.tags.ReturnStringList(), 1 )
	OutputFiles.FilesLock.release()

	wizard = MainFrame(None, APPTITLE, config.MaxImageBufSize, config.DefaultImageQuality, config.output, OutputFiles, TagsTracker, viewport)
	keybinds = KeyHandler()
	keybinds.AddList(config.keybinds)
	keybinds.RegisterObj(wizard)

	wizard.Show()
	app.MainLoop()

	OutputFiles.UpdateAll()
	OutputFiles.destroy()
	sys.exit(0)

if __name__ == '__main__':
	main()
