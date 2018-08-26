import sys
import traceback
import os
import os.path
import argparse
import json

import wx
from pubsub import pub
import jsonschema

from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import parser
from booruwizard.lib.fileops import FileManager
from booruwizard.ui.main import FileDialogFrame, MainFrame

APPNAME = 'booru-wizard'
APPVERSION = '0.1'
APPTITLE = ''.join( ( APPNAME, ' (', APPVERSION, ')' ) )

#TODO: Better accept dialog?
class ExceptDialog(wx.Dialog):
	def _OnClose(self, e):
		pub.sendMessage("EmergencyExit", message=None)
		e.Skip()
	def __init__(self, msg):
		wx.Dialog.__init__( self, None, title=''.join( (APPTITLE, ' - Exception') ),
							style=wx.CAPTION | wx.SYSTEM_MENU | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX )
		text = wx.TextCtrl(self, value= msg, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_NOHIDESEL | wx.TE_AUTO_URL)

		self.Bind(wx.EVT_CLOSE, self._OnClose)

def ExceptHook(etype, value, trace):
	frame = wx.GetApp().GetTopWindow()
	tmp = traceback.format_exception(etype, value, trace)
	exception = "".join(tmp)

	dialog = ExceptDialog(exception)
	dialog.ShowModal()
	dialog.Destroy()
sys.excepthook = ExceptHook

class MainError(Exception):
	def __init__(self, message):
		super(MainError, self).__init__(message)

class DialogSettings:
	def __init__(self, SchemaFile, ConfigFile, InputDir, OutputDir):
		self.EarlyExit = True
		self.SchemaFile = SchemaFile
		self.ConfigFile = ConfigFile
		self.InputDir = InputDir
		self.OutputDir = OutputDir
	def validate(self):
		if not os.path.exists(self.SchemaFile):
			raise MainError( ''.join( ('Schema file path: "', self.SchemaFile, '" does not exist.') ) )
		if not os.path.isfile(self.SchemaFile):
			raise MainError( ''.join( ('Schema file path: "', self.SchemaFile, '" is not a file.') ) )
		if not os.path.exists(self.ConfigFile):
			raise MainError( ''.join( ('Config file path: "', self.ConfigFile, '" does not exist.') ) )
		if not os.path.isfile(self.ConfigFile):
			raise MainError( ''.join( ('Config file path: "', self.ConfigFile, '" is not a file.') ) )
		if not os.path.exists(self.InputDir):
			raise MainError( ''.join( ('Input file path: "', self.InputDir, '" does not exist.') ) )
		if not os.path.isdir(self.InputDir):
			raise MainError( ''.join( ('Input file path: "', self.InputDir, '" is not a directory.') ) )
		if not os.path.exists(self.OutputDir):
			raise MainError( ''.join( ('Output file path: "', self.OutputDir, '" does not exist.') ) )
		if not os.path.isdir(self.OutputDir):
			raise MainError( ''.join( ('Output file path: "', self.OutputDir, '" is not a directory.') ) )

def ParseCommandLine():
	"Function to create a command line argument parser, and return the args object from it."
	parser = argparse.ArgumentParser(description='Get command line arguments.')
	parser.add_argument( '--no-dialog', '-d',  action='store_true', help='If this is set, then the file chooser dialog will not be displayed before the regular UI. Thus, the command line settings are relied upon.' )
	parser.add_argument( '--schema', '-s',  action='store', default='', help='Path to read schema file from. If none, then prompt it on software start.' )
	parser.add_argument( '--config', '-c', action='store', default='', help='Path to read config file from. If none, then prompt it on software start.' )
	parser.add_argument( '--input', '-i', action='store', default='', help='Path to input directory. If there is none, then prompt it on software start.' )
	parser.add_argument( '--output', '-o', action='store', default='', help='Path to output directory. If there is none, then then prompt it on software start.' )
	return parser.parse_args()

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
	if contents is None:
		return obj
	try:
		obj = json.loads(contents)
	except ValueError as err:
		raise MainError( ''.join( ('Failed to open file at path: "', path, '" Reason: "', err.msg, '" Line: ', err.lineno, ' Col: ', err.colno ) ) )
	return obj

def VerifyJSONSchema(path, obj, schema):
	"Function to validate a JSON object against a schema."
	try:
		jsonschema.validate(obj, schema)
	except jsonschema.ValidationError as err:
		raise MainError( ''.join( ('Failed to validate file at path: "', path, '" ', err.message) ) )

def GetDirFiles(DirPath):
	"Function to get all file paths from a directory."
	try:
		output = []
		for root, dirnames, filenames in os.walk(DirPath):
			output.extend(filenames)
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

	settings = DialogSettings(args.schema, args.config, args.input, args.output)
	if not args.no_dialog:
		dialog = FileDialogFrame(None, APPTITLE, settings)
		dialog.Show()
		app.MainLoop()
		if settings.EarlyExit:
			sys.exit(0)
	settings.validate()

	schema = ParseJSONFile(settings.SchemaFile)
	FilePaths = GetDirFiles(settings.InputDir)
	ImagePaths = GetFileTypes(FilePaths, VALID_IMAGES)
	JSONPaths = GetFileTypes(FilePaths, VALID_JSON)

	config = parser()
	config.parse( ReadTextFile(settings.ConfigFile) )

	OutputFiles = FileManager(config.MaxOpenFiles, config.UpdateInterval)
	OutputFiles.FilesLock.acquire()
	for p in ImagePaths:
		OutputFiles.AddFile(settings.InputDir, settings.OutputDir, p,
							config.DefaultName, config.DefaultSource, config.DefaultSafety, config.NamelessTags, config.SourcelessTags, config.TaglessTags)
	for p in JSONPaths:
		obj = ParseJSONFile( os.path.join(settings.InputDir, p) )
		VerifyJSONSchema(p, obj, schema)
		OutputFiles.AddJSON(settings.InputDir, settings.OutputDir, obj,
							config.DefaultName, config.DefaultSource, config.DefaultSafety, config.NamelessTags, config.SourcelessTags, config.TaglessTags)
	OutputFiles.StartUpdateTimer()

	TagsTracker = TagsContainer()
	for f in OutputFiles.ControlFiles:
		TagsTracker.AddContainer(f.tags)
	OutputFiles.FilesLock.release()

	wizard = MainFrame(None, APPTITLE, config.MaxImageBufSize, config.output, OutputFiles, config.ConditionalTags, TagsTracker)
	wizard.Show()
	app.MainLoop()

	OutputFiles.UpdateAll()
	OutputFiles.destroy()
	sys.exit(0)

if __name__ == '__main__':
	main()
