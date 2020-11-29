# Booru Wizard

This piece of software is meant to generate a wizard with which the user may choose metadata for various images. The metadata will be that associated with the various \*booru style sites; Danbooru, Gelbooru, etc.

So far, this entails:

* Title

* Source

* Safety rating

* Tags

Prompts displayed by the wizard can be manually determined by the user through the use of a configuration file. The default one included with this software is intended to be self-documenting, and explain the format, in addition to providing examples.

To anyone outside of the hair-fetish community, note that this default configuration file is specifically intended for organizing hair-fetish themed works. Should the software become more popular outside of this community, I might begin using a more generic default configuration.

Metadata output from this software is in a series of .json files which correspond to each image opened. They are given the same name, but with `.json` appended to them. When the software is restarted, these same files are read to restore its previous state.

This software was originally designed to be used in conjunction with the uploader userscript at: https://github.com/NetDenizen/Booru-mass-uploader

Other uploading options might be implemented later, largely depending on how well that option meets the needs of its users.

Finally, included with each release should be a file called `imgbrd-grabber_log_template.json`, which may be used as a template for the logging feature for imgbrd-grabber utility at https://github.com/Bionus/imgbrd-grabber to allow the software to import data from existing \*booru sites. Note that the `source` field will refer back to the original \*booru page, not the source listed in that page.

For reference is `output_schema.json`, which specifies the format which all metadata representations handled by the software must follow.

## Installation

These basic steps may be followed to get both the wizard software, and the uploader userscript installed and running.

### booru-wizard

1. Download the packaged version for your respective operating system. If in doubt, you should probably choose Windows 32-bit. These links will be updated on each release:

   * [Windows 64-bit](https://github.com/NetDenizen/booru-wizard/releases/download/2.0/booru-wizard-2.0-x86_64-windows.zip)
   * [Windows 32-bit](https://github.com/NetDenizen/booru-wizard/releases/download/2.0/booru-wizard-2.0-x86-windows.zip)
   * [Linux 64-bit](https://github.com/NetDenizen/booru-wizard/releases/download/2.0/booru-wizard-2.0-x86_64-linux.tar.gz)

2. Extract the archive to the directory of your choice.

3. `run.bat` (on Windows) or `run.sh` (on Linux) may be used to run the software with the default configuration file set, and will accept extra command line parameters. It is not at all necessary, and the `booru-wizard` executable may be run directly directly.

   The images directory is where the actual images you wish to manage should be. The software produces its output in a series of .json files which correspond to each image file; these are sent to the output JSON directory. Finally, output files may be reopened, to restore the settings of your previous session; the input JSON directory is searched for these.

   Please refer to the [Interface Guide](#interface-guide) section for more information on using the software.

### Booru-mass-uploader

1. Install a userscript manager for your browser. Common choices are Greasemonkey, Tampermonkey, and Violentmonkey are the 3 popular options. Thus far, the testing for this software has been with Greasemonkey on Mozilla browsers.

2. The script can be acquired [here](https://netdenizen.github.io/Booru-mass-uploader/booru.mass.uploader.user.js). You should know the userscript manager has recognized it, since it will create a popup prompting to install.

3. Go to the supported \*booru of your choice. Currently, Gelbooru 0.1, Danbooru, and Moebooru based sites should be supported, but note that this software was adapted from a preexisting project, and I've only tested Gelbooru for my version. If the script is loaded, you should see a 'Mass Upload' link at the top of the page, or in the navigation bar.

4. The page should be largely self-documenting, but a quick overview is that '.JSON files:' serves a similar role to the input JSON files option for the booru-wizard, and 'Image files:' a similarly equivalent roles. The images you wish to upload should be selected by 'Image files:', while the corresponding JSON files should be selected by '.JSON files:'.

## Interface Overview

![screenshot](https://i.imgur.com/1vQWVwu.png)

The image is divided into 3 panes, which can be resized within the window, by click-and-dragging the divider between them. Most elements should be marked with a tooltip (which is displayed when the element is hovered over with the mouse cursor).

## Building and Dependencies

The software is intended to run on Windows and Linux. A Mac port is a possibility, but it is a low priority, unless I find there is a great demand for it. Technically speaking, there is nothing in the code that I believe would make it incompatible, but I won't be actively maintaining and testing a port, for now. The library I used also seems to lack certain features on Mac.

Dependencies should not be an issue to the end-user, since the software will be packaged as a standalone executable along with the default configuration file, and a script to run the executable using that. Otherwise, the dependencies are:

* Python 3.4 or newer

* wxPython 4

* PyPubSub (Should be automatically included with wxPython)

* kanji_to_romaji3 (A Python 3 port I made of the kanji_to_romaji library, which can be found here: https://github.com/NetDenizen/kanji_to_romaji3)

* saucenao-api

* PyInstaller (For the officially supported build method.)

To satisfy all the dependencies, run:

```
python3 -m pip install --upgrade pip
python3 -m pip install wxPython PyPubSub PyInstaller saucenao_api
git clone https://github.com/NetDenizen/kanji_to_romaji3
cd kanji_to_romaji3
python3 -m pip install ./
```

To upgrade existing dependencies, run:

```
python3 -m pip install --upgrade pip wxPython PyPubSub PyInstaller saucenao_api
git clone https://github.com/NetDenizen/kanji_to_romaji3
cd kanji_to_romaji3
python3 -m pip install --upgrade ./
```

To build with PyInstaller, use this command from the root directory of the repository:

`python3 -m PyInstaller --clean --onefile --windowed --strip --name booru-wizard main.py`

Once booru-wizard is built, the generation of packages for distribution may be automated by running `make_package.sh` from the root directory of the repository. Example:

`./make_package.sh booru-wizard ./package /tmp 2.0 x86_64 linux`

To get usage information for the script, simply run it without arguments.

main.py can also be run directly with the booru-wizard files present in the same directory:

`python3 main.py`

## Development Roadmap

There are a number of features and changes which I consider for this software. These are listed both to solicit feedback from my users, and for my own planning.

### Unimplemented

* A color picker might be added to lend less ambiguity to the process of determining colors in images. A number of colors would be specified in the configuration file, and upon mousing over or clicking a pixel in the image, the closest 'match' among these colors would be shown.

* A scrollable menu of thumbnails for each image, which can be selected to change to a certain image might be handy for navigation. In the current state of the software, the user would need to remember the images by number, alone, to navigate to a specific one. (Note that the user can also search via path, now.)

* Currently, the software only identifies which files to open by their name, allowing the metadata files to freely be applied to any image. This could be considered a useful feature since the information can be readily copied and transferred between images. On the other hand, it could lead to mistaken application of metadata to the wrong image.

  The solution I consider is to implement some sort of hashing to identify images. This could be a complex component of the software itself, and I am not sure it is within the scope of purpose for the software to act as a search engine.

* The software produces JSON output that is fed into another utility to actually upload to a booru. Consider adding upload functionality directly to this software.

* Many settings pertaining to the operation of this software can be set in the configuration file before starting. Consider allowing more configuration while running the software, and the possibility of editing the configuration file from the software.

* Consider allowing the software to parse and write to different output formats than JSON. Perhaps SQLite?

* Consider adding metadata to the output files, which allow the software to more precisely recreate the state that it was in when those files were written. For instance, in ENTRY_QUESTION, tags can be added, however, the software does not know which tags to put in that entry question, when starting.

* Consider a system for adding keybinds to specific question fields (which do not normally have them).

* Consider replacing the tab navigation functionality with tab completion for autocomplete fields. The navigation could still be achieved with a modifier key.

* Consider a setting to clean the output files to rigorously conform to the specification.

* Consider a setting to make output directories, if they don't already exist. The file dialog is crippled in this regard on Linux

### Open

* I've considered adding more features to the image-viewer itself, such as the ability to zoom, and the ability to display animation. - Zooming implemented. Animation would likely involve complicated integration with ffmpeg libraries. wx animation support is too inconsistent between platforms. Specifically, the necessary methods are not supported for GTK.

* Currently, the software produces little in the way of command-line output which could be logged. What is logged, is typically from within the wxPython library. Aside from the command-line logging, such information could also be included in a window or other widget, or flushed to a file. - Basic command line logging implemented, especially for file operations. Are there any other places where we could add this?

* Consider fully implementing Gelbooru-style tag searching in the tag search field. - Negation using '-' is available. Consider adding '~' for 'OR' operations and parentheses to affect order of evaluation.

### Finished

* The displayed image is resized to fit its area and the algorithm used for this will distort it, somewhat. wxPython provides multiple choices of algorithm, and I hard-coded in the highest quality, but slowest one. Users with less powerful computers might benefit from the ability to change this. - Quality settings implemented.

* The 'sashes' which are dragged to resize the window panes are also a bit poorly defined. I can probably change that. There also appears to be an issue with selections being entirely hidden, rather than highlighted in the uneditable fields (7 and 9). - Sizing modified to make the 'sashes' more distinct.

* Normally, the software periodically updates its output files, in case it suddenly crashes before its normal closing procedure would be done. Currently, this process runs in the background without any feedback to the user. I consider adding some kind of indication for it. - Flush timer and button added.

* Especially in the case of imagesets, I consider that the same sequence of tags might be frequently repeated between multiple images. This raises the question as to if it should be possible to copy tags from one image to another. If not directly implemented, a string containing all tags, in a similar vein to the SESSION_TAGS option can be copy-and-pasted. - Implemented by SESSION_TAGS_IMPORTER, and BULK_TAGGER

* It may greatly improve memorization of keybinds by listing them in the tooltips for the relevant field. - Keybinds will now appear in tooltips, if they are present.

* Consider integrating the software with reverse image search services, to more efficiently identify sources. - Implemented by saucenao-api integration in SOURCE_QUESTION

* Overhaul the image display, so it does not suffer from extremely skewed aspect ratios when zoomed in. - The image display now uses the entire area, to show as much of the image as possible.

* Consider making the tag search field more interactive, so the user need not enter exact matches. - Added a second field to look up tag names using an autocomplete menu, and copy them to the image search menu.
