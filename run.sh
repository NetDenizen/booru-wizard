#!/bin/sh -e

# A POSIX-compliant shell-script to run the software with some default settings.
EXE_PATH='./booru-wizard'
SCHEMA='./default_schema.json'
CONFIG='./default_config.txt'
INPUT=''
OUTPUT=''

"$EXE_PATH" --schema "$SCHEMA" --config "$CONFIG" --input "$INPUT" --output "$OUTPUT"
