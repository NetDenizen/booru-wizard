# Changelog

## TODO-TO-DO 2.0

* SOURCELESS_TAGS are now added on an empty source, as well as an unset one.

* Implement NATIVE_TAGS.

* Add a '--json-compact' or '-C' option, and a complementary opening dialog box to allow the user to choose between pretty-printed and compact JSON output.

* Add a BLANK_QUESTION to use as an organizational tool.

* Recursive aliasing system. Now aliased tags will trigger other aliases. Circular aliases will also be handled without errors.

* SESSION_TAG_IMPORTER now starts will all options unchecked, and with a button to toggle all checks.

* SESSION_TAG_IMPORTER now sets imported tags to 'user' set.

* The program will now preserve arbitrary values associated with each file in the JSON output format, instead of overwriting them to rigorously match the specification.

* The valid options for 'rating' in the output data files are 'safe', 'questionable', and 'explicit'. Their single-letter equivalents of 's', 'q', and 'e' are no longer supported.

* The current path is no longer redundantly listed in path selection menus.

* Fix crash when opening an image path autocomplete menu with a keybind.

* Load longest matching path in the image autocomplete menus, instead of the shortest.

* List all paths in image path selection menus, if the current contents are an exact match.

* Report parser errors with line and column numbers starting at 1.

* Include image indexes in image path search.

* Remove pointless "Use this..." checkboxes from NAME_QUESTION and SOURCE_QUESTION.

* More interactivity from the user interface. Buttons are grayed out more when their function does no purpose. The cursor changes when clicking and dragging in the image display.

* Tooltips are now used extensively to document the software, instead of a marked screenshot.

* Implement CUSTOM_TAGS.

* Implement IMAGE_CONDITION_CONDITION and IMAGE_CONDITION_TAGS.

* Implement ADDED_TAGS and ADDED_TAGS_ENTRY

* Refine contents of imgbrd-grabber_log_template.json to use %sources% for the source field, instead of %url_page%.

* We not preview the contents of the question in the question search menu.

* Implement SOURCE_QUESTION_PATTERN and SOURCE_QUESTION_REPLACEMENT.

* Implement path format replacement for SOURCE_QUESTION.

* Implement BULK_TAGGER.

* The DEFAULT_SAFETY setting is case-insensitive.

* Implement path searching for SESSION_TAGS_IMPORTER.

* Allow locking a question so it is used in the next image that's changed to.

* Massive overhaul of default_config.cfg

* Significant refactoring to reduce redundant code, and simplify addition of new features.

* Fix many, many bugs.

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
