import os.path
import argparse
import csv
from collections import OrderedDict

from booruwizard.lib.template import parser, OptionQuestion

class TagEntry:
	def AddDesc(self, desc):
		if desc and desc not in self.descs:
			self.descs.append(desc)
	def AddAliases(self, aliases):
		for a in aliases:
			if a not in self.aliases:
				self.aliases.append(a)
	def AddCategory(self, category):
		if category and category not in self.categories:
			self.categories.append(category)
	def GetNameString(self):
		return self.name
	def GetDescsString(self):
		return ', '.join(self.descs)
	def GetAliasesString(self):
		return ' '.join(self.aliases)
	def GetCategoriesString(self):
		return ', '.join(self.categories)
	def __init__(self, name):
		self.name = name
		self.descs = []
		self.aliases = []
		self.categories = []

class TagsRecord:
	def _WriteRow(self, t):
		row = {}
		row['Tag Name'] = t.GetNameString()
		row['Tag Description'] = t.GetDescsString()
		if self.WriteCategories:
			row['Categories'] = t.GetCategoriesString()
		row['Tag Aliases To'] = t.GetAliasesString()
		self.writer.writerow(row)
	def write(self):
		for n, t in self.tags.items():
			self._WriteRow(t)
	def AddTag(self, name, desc, aliases, category):
		if not name:
			return
		t = self.tags.get(name.lower(), None)
		if t is None:
			t = TagEntry(name)
			self.tags[name] = t
		t.AddDesc(desc)
		t.AddAliases(aliases)
		t.AddCategory(category)
	def __init__(self, WriteCategories, writer):
		self.WriteCategories = WriteCategories
		self.writer = writer
		self.tags = OrderedDict()

def ParseCommandLine():
	"Function to create a command line argument parser, and return the args object from it."
	ArgParser = argparse.ArgumentParser(description='Get command line arguments.')
	ArgParser.add_argument('--input', '-i', action='store', default='', required=True, help='Path to the image input directory.')
	ArgParser.add_argument('--output', '-o', action='store', default='', required=True, help='Path to the JSON output directory. If none, then copy it will be copied from "--json-input".')
	ArgParser.add_argument('--overwrite', '-O', action='store_true', help='Overwrite the output file if it already exists.')
	ArgParser.add_argument('--trim-desc', '-t', action='store_true', help='Remove whitespace, dashes, and the name of the tag from its description text.')
	ArgParser.add_argument('--suppress-categories', '-c', action='store_true', help="Do not include a 'categories' field with the output.")
	ArgParser.add_argument('--suppress-question-tags', '-1', action='store_true', help='Do not write those tags which are part of wizard questions (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-nameless-tags', '-2', action='store_true', help='Do not write those tags which are used if a name is unspecified for an image (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-sourceless-tags', '-3', action='store_true', help='Do not write those tags which are used if a source is unspecified for an image (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-tagless-tags', '-4', action='store_true', help='Do not write those tags which are used if other tags are unspecified for an image (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-image-condition-tags', '-5', action='store_true', help='Do not write those tags which are used if a source is unspecified for an image (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-alias-source-tags', '-6', action='store_true', help='Do not write those tags which are aliased to other tags (though they may be included from elsewhere).')
	ArgParser.add_argument('--suppress-alias-destination-tags', '-7', action='store_true', help='Do not write those tags which are used as aliases for other tags (though they may be included from elsewhere).')
	return ArgParser.parse_args()

def OpenOutputFile(path, overwrite):
	if overwrite or not os.path.exists(path):
		return open(path, 'w')
	else:
		raise FileExistsError( ''.join( (path, ' already exists! Use -O to overwrite.') ) )

def ParseInputFile(path):
	config = parser()
	File = open(path, 'r')
	config.parse( File.read() )
	File.close()
	return config

def GetConditionalTags(config, name):
	found = config.ConditionalTags.AllNodes.GetNode( name.lower() )
	if found:
		return found.GetChildNames([])
	else:
		return []

def GetTrimmedDesc(text, tag, trim_desc):
	if not trim_desc or not tag:
		return text
	NewText = text
	while True:
		NewText = NewText.lstrip()
		if NewText.startswith(tag) or NewText.startswith( tag.lower() ):
			NewText = NewText[len(tag):]
		elif NewText.startswith('-'):
			NewText = NewText[len('-'):]
		else:
			break
	return NewText

def RecordQuestionTags(suppress, record, config, trim_desc):
	if suppress:
		return
	for q in config.output:
		if not isinstance(q, OptionQuestion):
			continue
		for o in q.options:
			record.AddTag(o.tag, GetTrimmedDesc(o.name, o.tag, trim_desc), GetConditionalTags(config, o.tag), 'Question Tags')

def RecordXTags(suppress, record, config, X, category):
	if suppress:
		return
	for t in X:
		record.AddTag(t, '', GetConditionalTags(config, t), category)

def RecordNamelessTags(suppress, record, config):
	RecordXTags(suppress, record, config, config.NamelessTags.ReturnStringList(), 'Nameless Tags')

def RecordSourcelessTags(suppress, record, config):
	RecordXTags(suppress, record, config, config.SourcelessTags.ReturnStringList(), 'Sourceless Tags')

def RecordTaglessTags(suppress, record, config):
	RecordXTags(suppress, record, config, config.TaglessTags.ReturnStringList(), 'Tagless Tags')

def RecordImageConditionTags(suppress, record, config):
	if suppress:
		return
	for c in config.ImageConditions:
		for t in c.TagString.split():
			record.AddTag(t, '', GetConditionalTags(config, t), 'Image Condition Tags')

def RecordAliasSourceTags(suppress, record, config):
	if suppress:
		return
	for n in config.ConditionalTags.AllNodes.nodes:
		if n.nodes:
			record.AddTag(n.name, '', GetConditionalTags(config, n.name), 'Alias Source Tags')

def RecordAliasDestinationTags(suppress, record, config):
	if suppress:
		return
	for n in config.ConditionalTags.AllNodes.nodes:
		if n.nodes:
			for cn in n.nodes:
				record.AddTag(cn.name, '', GetConditionalTags(config, cn.name), 'Alias Destination Tags')

def main():
	args = ParseCommandLine()

	config = ParseInputFile(args.input)
	handle = OpenOutputFile(args.output, args.overwrite)

	if not args.suppress_categories:
		fieldnames = ['Tag Name', 'Tag Description', 'Categories', 'Tag Aliases To']
	else:
		fieldnames = ['Tag Name', 'Tag Description', 'Tag Aliases To']

	writer = csv.DictWriter(handle, fieldnames)
	writer.writeheader()

	record = TagsRecord(not args.suppress_categories, writer)
	RecordQuestionTags(args.suppress_question_tags, record, config, args.trim_desc)
	RecordNamelessTags(args.suppress_nameless_tags, record, config)
	RecordSourcelessTags(args.suppress_sourceless_tags, record, config)
	RecordTaglessTags(args.suppress_tagless_tags, record, config)
	RecordImageConditionTags(args.suppress_image_condition_tags, record, config)
	RecordAliasSourceTags(args.suppress_alias_source_tags, record, config)
	RecordAliasDestinationTags(args.suppress_alias_destination_tags, record, config)
	record.write()
	handle.close()

if __name__ == '__main__':
	main()
