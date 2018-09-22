# A batch file to run the software with some default settings.
@ECHO OFF

SET EXE_PATH="%cd%\booru-wizard"
SET SCHEMA="%cd%\default_schema.json"
SET CONFIG="%cd%\default_config.txt"
SET INPUT=""
SET OUTPUT=""

%EXE_PATH% --schema "%SCHEMA%" --config "%CONFIG%" --input "%INPUT%" --output "%OUTPUT%"
