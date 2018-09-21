# Booru Wizard

This piece of software is meant to generate a wizard with which the user may choose metadata for various images. The metadata will be that associated with the various \*booru style sites; Danbooru, Gelbooru, etc.

So far, this entails:

* Title

* Source

* Safety rating

* Tags

Prompts displayed by the wizard can be manually determined by the user through the use of a configuration file. The default one included with this software is intended to be self-documenting, and show explain the format, in addition to providing examples.

To anyone outside of the hair-fetish community, note that this default configuration file is specifically intended for organizing hair-fetish themed works. Should the software become more popular outside of this community, I might begin using a more generic default configuration.

## Interface Guide

The basic interface of the software is as follows; each element is annotated with a green number:

![screenshot](https://i.imgur.com/3EZ6VYU.png)

The image is divided into 3 panes, which can be resized within the window, by click-and-dragging the space between them. Note that text boxes with the same color as the background are not editable.

1. The name of the software and its current version.

2. The number of the current image.

3. The name of the current image.

4. The number of the current question.

5. The current image is overlaid on a black square.

6. The name of the current image.

7. The number of the current image. This can be changed to select an arbitrary one.

8. The instructions or prompt for the current question are in this text box.

9. The number of the current question. This can be changed to select an arbitrary one.

10. Change to the 'left', or previous image.

11. Change to the 'left', or previous question.

11. Change to the 'right', or previous image.

13. Change to the 'right', or previous question.

14. The field in which the prompt at element 8 is filled. It can either be a text box, checklist, or radio-buttons.

## Installation, Building, and Dependencies

The software is intended to run on Windows and Linux. A Mac port is a possibility, but it is a low priority, unless I find there is a great demand for it. Technically speaking, there is nothing in the code that I believe would make it incompatible, but I won't be actively maintaining and testing a port, for now. The library I used also seems to lack certain features on Mac.

Dependencies should not be an issue to the end-user, since the software will be packaged as a standalone executable. Otherwise, the dependencies are:

* Python 3.2 or newer

* wxPython 4

* PyPubSub (Should be autmatically included with wxPython)

* jsonschema

To build with PyInstaller, use this command from the root directory of the repository:

`pyinstaller --clean --onefile --windowed --strip --name booru-wizard main.py`
