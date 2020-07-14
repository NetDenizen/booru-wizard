"Main procedure of software."

import sys
import traceback
import os
import os.path
import argparse
import json
from collections import OrderedDict

import wx
from pubsub import pub

from booruwizard.lib.tag import TagsContainer
from booruwizard.lib.template import parser, OptionQuestion
from booruwizard.lib.fileops import FileManager
from booruwizard.lib.viewport import ViewPort
from booruwizard.lib.keyhandler import KeyHandler
from booruwizard.lib.imagereader import ImageReader
from booruwizard.ui.main import FileDialogFrame, MainFrame

APPNAME = 'booru-wizard'
APPVERSION = '2.0'
APPTITLE = ''.join( (APPNAME, ' (', APPVERSION, ')') )

#TODO: Better accept dialog?
class ExceptDialog(wx.Dialog):
	def _OnClose(self, e):
		pub.sendMessage("EmergencyExit", message = None)
		e.Skip()
	def __init__(self, msg):
		wx.Dialog.__init__(self, None, title=''.join( (APPTITLE, ' - Exception') ),
						   style=wx.CAPTION | wx.SYSTEM_MENU | wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
		text = wx.TextCtrl(self, value= msg, style= wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.TE_NOHIDESEL | wx.TE_AUTO_URL)
		text.SetBackgroundColour( wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK) )
		self.Bind(wx.EVT_CLOSE, self._OnClose)

def ExceptHook(etype, value, trace):
	tmp = traceback.format_exception(etype, value, trace)
	exception = ''.join(tmp)

	wx.LogError( exception.replace('%', '%%') )
	dialog = ExceptDialog(exception)
	dialog.ShowModal()
	dialog.Destroy()
sys.excepthook = ExceptHook

class MainError(Exception):
	pass

class DialogSettings:
	def __init__(self, ConfigFile, ImageInputDir, JSONInputDir, JSONOutputDir):
		self.EarlyExit = True
		self.ConfigFile = ConfigFile
		self.ImageInputDir = ImageInputDir
		self.JSONInputDir = JSONInputDir
		self.JSONOutputDir = JSONOutputDir
	def validate(self):
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
	ArgParser.add_argument('--verbose', '-v', action='store_true', help='If this is set, then the program will produce verbose logging output.')
	ArgParser.add_argument('--no-dialog', '-d', action='store_true', help='If this is set, then the file chooser dialog will not be displayed before the regular UI. Thus, the command line settings are relied upon.')
	ArgParser.add_argument('--config', '-c', action='store', default='', help='Path to read config file from.')
	ArgParser.add_argument('--image-input', '-i', action='store', default='', help='Path to the image input directory.')
	ArgParser.add_argument('--json-input', '-j', action='store', default='', help='Path to the JSON input directory. If none, then it will be copied from "--image-input".')
	ArgParser.add_argument('--json-output', '-o', action='store', default='', help='Path to the JSON output directory. If none, then copy it will be copied from "--json-input".')
	return ArgParser.parse_args()

def ReadTextFile(path):
	"Function to open a text file, and return the string from its contents."
	contents = None
	try:
		File = open(path, 'r')
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
def GetFileTypes(paths, extensions):
	"Function to get those paths which certain extensions specified in a list, and return them."
	output = []
	for p in paths:
		if os.path.splitext(p)[1].lower() in extensions:
			output.append(p)
	return output

def main():
	"Main procedure."
	#TODO: Tidy this the fuck up.

	app = wx.App()
	wx.Log.SetActiveTarget( wx.LogStderr() )
	args = ParseCommandLine()
	if args.verbose:
		wx.Log.SetVerbose()

	settings = DialogSettings(args.config, args.image_input, args.json_input, args.json_output)
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

	ImagePaths = GetFileTypes(GetDirFiles(settings.ImageInputDir), VALID_IMAGES)
	JSONPaths = GetFileTypes(GetDirFiles(settings.JSONInputDir), VALID_JSON)

	wx.LogMessage( ''.join( ("Reading config at file at '", settings.ConfigFile.replace('%', '%%'), "'") ) )
	config = parser()
	config.parse( ReadTextFile(settings.ConfigFile) )

	images = ImageReader(config.MaxImageBufSize)

	viewport = ViewPort(config.BackgroundColor1, config.BackgroundColor2, config.BackgroundSquareWidth,
						config.StartZoomInterval, config.ZoomAccel, config.ZoomAccelSteps, config.PanInterval)

	TagsTracker = TagsContainer()
	for q in config.output:
		if not isinstance(q, OptionQuestion):
			continue
		for t in q.GetChoiceTags():
			TagsTracker.RegisterConfig(t)
	for t in config.NamelessTags.ReturnStringList():
		TagsTracker.RegisterConfig(t)
	for t in config.SourcelessTags.ReturnStringList():
		TagsTracker.RegisterConfig(t)
	for t in config.TaglessTags.ReturnStringList():
		TagsTracker.RegisterConfig(t)
	for c in config.ImageConditions:
		for t in c.TagString.split():
			TagsTracker.RegisterConfig(t)
	for t in config.ConditionalTags.lookup.keys():
		TagsTracker.RegisterConfig(t)

	OutputFiles = FileManager(config.MaxOpenFiles, config.UpdateInterval)
	OutputFiles.FilesLock.acquire()
	for p in ImagePaths:
		OutputFiles.AddFile(settings.JSONOutputDir, p,
							config.DefaultName, config.DefaultSource, config.DefaultSafety,
							config.ConditionalTags, config.NamelessTags, config.SourcelessTags, config.TaglessTags)
	for p in JSONPaths:
		obj = ParseJSONFile( os.path.join(settings.JSONInputDir, p) )
		OutputFiles.AddJSON(settings.ImageInputDir, settings.JSONOutputDir, obj,
							config.DefaultName, config.DefaultSource, config.DefaultSafety,
							config.ConditionalTags, config.NamelessTags, config.SourcelessTags, config.TaglessTags)

	if not OutputFiles.ControlFiles:
		raise MainError('No input files found.')

	for f in OutputFiles.ControlFiles:
		TagsTracker.AddStringList(f.tags.ReturnStringList(), 1)

	images.AddPathsList(OutputFiles.InputPaths)
	for i, f in reversed( list( enumerate(OutputFiles.ControlFiles) ) ):
		for c in config.ImageConditions:
			if images.load(i).CheckImageCondition(c.condition):
				f.PrepareChange()
				if not f.tags.HasAnyOfString(c.TagString):
					TagsTracker.AddString(c.TagString, 1)
				f.tags.SetString(c.TagString, 1)
				f.SetConditionalTags(c.TagString)
				f.SetTaglessTags()
				f.FinishChange()
	OutputFiles.FilesLock.release()

	wx.LogMessage('Main window opened.')
	wizard = MainFrame(None, APPTITLE, images, config.DefaultImageQuality, config.output, OutputFiles, TagsTracker, viewport)
	wizard.Bind(wx.EVT_CLOSE, OutputFiles.OnExit) #XXX: Windows for some reason prints log messages to popup windows, instead of stderr, after the main loop ends. We destroy OutputFiles

	keybinds = KeyHandler()
	keybinds.AddList(config.keybinds)
	keybinds.RegisterObj(wizard)

	wizard.Show()
	app.MainLoop()
	wx.LogMessage('Main window closed.')

	sys.exit(0)

if __name__ == '__main__':
	main()
