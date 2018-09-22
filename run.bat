:: A batch file to run the software with some default settings.
@ECHO OFF

Set EXE_PATH="%cd%\booru-wizard"
Set SCHEMA="%cd%\default_schema.json"
Set CONFIG="%cd%\default_config.txt"
Set INPUT=
Set OUTPUT=

start "" "%EXE_PATH%" --schema "%SCHEMA%" --config "%CONFIG%" --input "%INPUT%" --output "%OUTPUT%"
