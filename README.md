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

## Installation

These basic steps may be followed to get both the wizard software, and the uploader userscript installed and running.

### booru-wizard

1. Download the packaged version for your respective operating system. These links will be updated on each release:

   * [Windows 64-bit](https://github.com/NetDenizen/booru-wizard/releases/download/0.3/booru-wizard-0.3-x86_64-windows.zip)
   * [Windows 32-bit](https://github.com/NetDenizen/booru-wizard/releases/download/0.3/booru-wizard-0.3-x86-windows.zip)
   * [Linux 64-bit](https://github.com/NetDenizen/booru-wizard/releases/download/0.3/booru-wizard-0.3-x86_64-linux.tar.gz)

2. Extract the archive to the directory of your choice.

3. `run.bat` (on Windows) or `run.sh` (on Linux) may be used to run the software with the default schema and configuration files set. It is not at all necessary, and the `booru-wizard` executable may be run directly directly.

   The images directory is where the actual images you wish to manage should be. The software produces its output in a series of .json files which correspond to each image file; these are sent to the output JSON directory. Finally, output files may be reopened, to restore the settings of your previous session; the input JSON directory is searched for these.

   Please refer to the [Interface Guide](#interface-guide) section for more information on using the software.

### Booru-mass-uploader

1. Install a userscript manager for your browser. Common choices are Greasemonkey, Tampermonkey, and Violentmonkey are the 3 popular options. Thus far, the testing for this software has been with Greasemonkey on Mozilla browsers.

2. The script can be acquired [here](https://netdenizen.github.io/Booru-mass-uploader/booru.mass.uploader.user.js). You should know the userscript manager has recognized it, since it will create a popup prompting to install.

3. Go to the supported \*booru of your choice. Currently, Gelbooru 0.1, Danbooru, and Moebooru based sites should be supported, but note that this software was adapted from a preexisting project, and I've only tested Gelbooru for my version. If the script is loaded, you should see a 'Mass Upload' link at the top of the page, or in the navigation bar.

4. The page should be largely self-documenting, but a quick overview is that '.JSON files:' serves a similar role to the input JSON files option for the booru-wizard, and 'Image files:' a similarly equivalent roles. The images you wish to upload should be selected by 'Image files:', while the corresponding JSON files should be selected by '.JSON files:'.

## Interface Guide

The basic interface of the software is as follows; each element is annotated with a green number:

![screenshot](https://i.imgur.com/IQuJNa9.png)

The image is divided into 3 panes, which can be resized within the window, by click-and-dragging the space between them. Note that text boxes with the same color as the background are not editable.

1. The name of the software and its current version.

2. The number of the current image.

3. The name of the current image.

4. The number of the current question.

5. The resolution of the current image.

6. The current image is overlaid on checkered transparency background.

7. The name of the current image. The default keybind to select the field is F9.

8. The number of the current image. This can be changed to select an arbitrary one. The default keybind to select the field is F6.

9. The instructions or prompt for the current question are in this text box. The default keybind to select the field is F8.

10. The number of the current question. This can be changed to select an arbitrary one. The default keybind to select the field is F7.

11. Change to the 'left', or previous image. Default equivalent keybind is F1.

12. Change to the 'left', or previous question. Default equivalent keybind is F2.

13. Change to the 'right', or next image. Default equivalent keybind is F3.

14. Change to the 'right', or next question. Default equivalent keybind is F4.

15. The field in which the prompt at element 8 is filled. It can either be a text box, checklist, or radio-buttons. The default keybind to accept it is F5.

## Building and Dependencies

The software is intended to run on Windows and Linux. A Mac port is a possibility, but it is a low priority, unless I find there is a great demand for it. Technically speaking, there is nothing in the code that I believe would make it incompatible, but I won't be actively maintaining and testing a port, for now. The library I used also seems to lack certain features on Mac.

Dependencies should not be an issue to the end-user, since the software will be packaged as a standalone executable along with the configuration file, schema file, and a script to run the executable using those other files. Otherwise, the dependencies are:

* Python 3.2 or newer

* wxPython 4

* PyPubSub (Should be autmatically included with wxPython)

* jsonschema

* kanji_to_romaji3 (A Python 3 port I made of the kanji_to_romaji library, which can be found here: https://github.com/NetDenizen/kanji_to_romaji3)

To build with PyInstaller, use this command from the root directory of the repository:

`pyinstaller --clean --onefile --windowed --strip --name booru-wizard main.py`

main.py can also be run directly with the booru-wizard files present in the same directory:

`python3 main.py`

## Development Roadmap

There are a number of features and changes which I consider for this software. These are listed both to solicit feedback from my users, and for my own planning. In no specific order, they are:

* The displayed image is resized to fit its area and the algorithm used for this will distort it, somewhat. wxPython provides multiple choices of algorithm, and I hard-coded in the highest quality, but slowest one. Users with less powerful computers might benefit from the ability to change this.

* A color picker might be added to lend less ambiguity to the process of determining colors in images. A number of colors would be specified in the configuration file, and upon mousing over or clicking a pixel in the image, the closest 'match' among these colors would be shown.

* Especially in the case of imagesets, I consider that the same sequence of tags might be frequently repeated between multiple images. This raises the question as to if it should be possible to copy tags from one image to another. If not directly implemented, a string containing all tags, in a similar vein to the SESSION_TAGS option can be copy-and-pasted.

* I've considered adding more features to the image-viewer itself, such as the ability to zoom, and the ability to display animation.

* Currently, the software produces little in the way of command-line output which could be logged. What is logged, is typically from within the wxPython library. Aside from the command-line logging, such information could also be included in a window or other widget, or flushed to a file.

* A scrollable menu of thumbnails for each image, which can be selected to change to a certain image might be handy for navigation. In the current state of the software, the user would need to remember the images by number, alone, to navigate to a specific one.

* The 'sashes' which are dragged to resize the window panes are also a bit poorly defined. I can probably change that. There also appears to be an issue with selections being entirely hidden, rather than highlighted in the uneditable fields (7 and 9).

* Normally, the software periodically updates its output files, in case it suddenly crashes before its normal closing procedure would be done. Currently, this process runs in the background without any feedback to the user. I consider adding some kind of indication for it.

* Currently, the software only identifies which files to open by their name, allowing the metadata files to freely be applied to any image. This could be considered a useful feature since the information can be readily copied and transferred between images. On the other hand, it could lead to mistaken application of metadata to the wrong image.

  The solution I consider is to implement some sort of hashing to identify images. This could be a complex component of the software itself, and I am not sure it is within the scope of purpose for the software to act as a search engine.
