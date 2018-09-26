:: A batch file to run the software with some default settings.
@ECHO OFF

Set EXE_PATH="%cd%\booru-wizard"
Set SCHEMA="%cd%\default_schema.json"
Set CONFIG="%cd%\default_config.txt"
set IMAGE_INPUT=
set JSON_INPUT=
set JSON_OUTPUT=

start "" "%EXE_PATH%" --schema "%SCHEMA%" ^
					  --config "%CONFIG%" ^
					  --image-input "%IMAGE_INPUT%" ^
					  --json-input "%JSON_INPUT%" ^
					  --json-output "%JSON_OUTPUT%"
