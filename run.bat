:: A batch file to run the software with some default settings.
@echo off

set EXE_PATH="%cd%\booru-wizard.exe"
set CONFIG="%cd%\default_config.cfg"
set IMAGE_INPUT=
set JSON_INPUT=
set JSON_OUTPUT=

:: extra_args can be set to include arguments which override those which came before it.
:: Should command line arguments be passed to this script, they will take the place of those.
set extra_args=
if not [%*] == [] set extra_args="%*"

start "" "%EXE_PATH%" --config "%CONFIG%" ^
					  --image-input "%IMAGE_INPUT%" ^
					  --json-input "%JSON_INPUT%" ^
					  --json-output "%JSON_OUTPUT%" ^
					  %extra_args%
