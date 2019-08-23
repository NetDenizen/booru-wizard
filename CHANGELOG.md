# Changelog

## 2019-08-22 1.1

* Search results for question prompts should now contain all choices, by if empty.

* Fix inclusion of '%' character in log messages.

* Options in config files are not case-insensitive.

* Minor refactoring and rewording of default configuration

## 2019-04-29 1.0

* Countless fixes, refinements, and optimizations.

* Revised keybinds, and tags in default config.

* Display image cache statistics, and file size.

* Sort filenames opened by software.

* Kana Romanization for text entry based wizard questions.

* Add image quality control settings.

* Add timer display and button for flushing changes to hard drive.

* Add the means to read data from imgbrd-grabber (https://github.com/Bionus/imgbrd-grabber) logs.

* Align all controls to the left side of the screen.

* List tags by their state (not set, automatically set, and manually set).

* Implement zoomable image display.

* Add the SESSION_TAGS_IMPORTER wizard type.

* Implement logging of messages to stderr.

* Allow entering images by path, and autocomplete to assist with this.

* Implement searching for questions by keywords in their prompt text.

* ENTRY_QUESTION and IMAGE_TAGS_ENTRY are now multiline!

* Remove jsonschema related options and dependency. `default_schema.json` is renamed to `output_schema.json` for reference purposes.

* `tags` field of JSON format now performs function of `TagStrings`, which has been removed. Old `tags` is no longer supported!

* The run scripts now accept command line arguments.

## 2018-10-27 0.3

* Revise run.sh to allow spaces and other special characters in the EXE path.

* Create separate image input, JSON input, and JSON output directory settings.

* Revise layout spacing.

* Change background of radio-button based questions to match that of checkbox based questions.

* Improve documentation.

* Rename default_config.txt to default_config.cfg

* Add checkered background for transparent images.

* Add keybind support.

* Add IMAGE_TAGS_ENTRY

* Add checkbox to NAME_QUESTION to better match SOURCE_QUESTION

* Add resolution display.

* Revise JSON output files to store tag information in a more space-efficient manner. The software is still backwards compatible with the old method.

## 2018-09-21 0.2

* First formal release.
