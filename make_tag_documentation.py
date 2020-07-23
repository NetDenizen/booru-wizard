import os.path
import argparse
import csv
from booruwizard.lib.template import parser, OptionQuestion

def ParseCommandLine():
	"Function to create a command line argument parser, and return the args object from it."
	ArgParser = argparse.ArgumentParser(description='Get command line arguments.')
	ArgParser.add_argument('--input', '-i', action='store', default='', required=True, help='Path to the image input directory.')
	ArgParser.add_argument('--output', '-o', action='store', default='', required=True, help='Path to the JSON output directory. If none, then copy it will be copied from "--json-input".')
	ArgParser.add_argument('--overwrite', '-O', action='store_true', help='Overwrite the output file if it already exists.')
	ArgParser.add_argument('--trim-desc', '-t', action='store_true', help='Remove whitespace, dashes, and the name of the tag from its description text.')
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
		return ' '.join( found.GetChildNames([]) )
	else:
		return ''

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

def WriteRow(AddedTags, writer, config, tag, desc):
	TagLower = tag.lower()
	if not TagLower or TagLower in AddedTags:
		return
	AddedTags.add(TagLower)
	row = {}
	row['Tag Name'] = TagLower
	row['Tag Description'] = desc
	row['Tag Aliases To'] = GetConditionalTags(config, TagLower)
	writer.writerow(row)

def WriteQuestionTags(AddedTags, config, writer, trim_desc):
	for q in config.output:
		if not isinstance(q, OptionQuestion):
			continue
		for o in q.options:
			WriteRow( AddedTags, writer, config, o.tag, GetTrimmedDesc(o.name, o.tag, trim_desc) )

def WriteXTags(AddedTags, config, X, writer):
	for t in X:
		WriteRow(AddedTags, writer, config, t, '')

def WriteNamelessTags(AddedTags, config, writer):
	WriteXTags(AddedTags, config, config.NamelessTags.ReturnStringList(), writer)

def WriteSourcelessTags(AddedTags, config, writer):
	WriteXTags(AddedTags, config, config.SourcelessTags.ReturnStringList(), writer)

def WriteTaglessTags(AddedTags, config, writer):
	WriteXTags(AddedTags, config, config.TaglessTags.ReturnStringList(), writer)

def WriteImageConditionTags(AddedTags, config, writer):
	for c in config.ImageConditions:
		for t in c.TagString.split():
			WriteRow(AddedTags, writer, config, t, '')

def WriteAliasTags(AddedTags, config, writer):
	WriteXTags(AddedTags, config, config.ConditionalTags.AllNodes.GetChildNames([]), writer)

def main():
	args = ParseCommandLine()

	config = ParseInputFile(args.input)
	handle = OpenOutputFile(args.output, args.overwrite)

	fieldnames = ['Tag Name', 'Tag Description', 'Tag Aliases To']
	writer = csv.DictWriter(handle, fieldnames)
	writer.writeheader()

	AddedTags = set()
	WriteQuestionTags(AddedTags, config, writer, args.trim_desc)
	WriteNamelessTags(AddedTags, config, writer)
	WriteSourcelessTags(AddedTags, config, writer)
	WriteTaglessTags(AddedTags, config, writer)
	WriteImageConditionTags(AddedTags, config, writer)
	WriteAliasTags(AddedTags, config, writer)
	handle.close()

if __name__ == '__main__':
	main()
