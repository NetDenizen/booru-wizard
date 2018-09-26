#!/bin/sh -e

# A POSIX-compliant shell-script to run the software with some default settings.
EXE_PATH='./booru-wizard'
SCHEMA='./default_schema.json'
CONFIG='./default_config.cfg'
IMAGE_INPUT=''
JSON_INPUT=''
JSON_OUTPUT=''

"$EXE_PATH" --schema "$SCHEMA" \
			--config "$CONFIG" \
			--image-input "$IMAGE_INPUT" \
			--json-input "$JSON_INPUT" \
			--json-output "$JSON_OUTPUT"
