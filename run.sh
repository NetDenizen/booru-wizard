#!/bin/sh -e

# A POSIX-compliant shell-script to run the software with some default settings.
EXE_PATH='./booru-wizard'
CONFIG='./default_config.cfg'
IMAGE_INPUT=''
JSON_INPUT=''
JSON_OUTPUT=''

# extra_args can be set to include arguments which override those which came before it.
# Should command line arguments be passed to this script, they will take the place of those.
extra_args=''
if [ $# -ne 0 ]
then
	DEFAULT_IFS=$IFS
	IFS=' '
	extra_args="$*"
	IFS=$DEFAULT_IFS
fi

"$EXE_PATH" --config "$CONFIG" \
			--image-input "$IMAGE_INPUT" \
			--json-input "$JSON_INPUT" \
			--json-output "$JSON_OUTPUT" \
			$extra_args
