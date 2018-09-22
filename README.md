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

Dependencies should not be an issue to the end-user, since the software will be packaged as a standalone executable along with the configuration file, schema file, and a script to run the executable using those other files. Otherwise, the dependencies are:

* Python 3.2 or newer

* wxPython 4

* PyPubSub (Should be autmatically included with wxPython)

* jsonschema

To build with PyInstaller, use this command from the root directory of the repository:

`pyinstaller --clean --onefile --windowed --strip --name booru-wizard main.py`

main.py can also be run directly with the booru-wizard files present in the same directory:

`python3 main.py`

## Development Roadmap

There are a number of features and changes which I consider for this software. These are listed both to solicit feedback from my users, and for my own planning. In no specific order, they are:

* The displayed image is resized to fit its area and the algorithm used for this will distort it, somewhat. wxPython provides multiple choices of algorithm, and I hard-coded in the highest quality, but slowest one. Users with less powerful computers might benefit from the ability to change this.

* A major feature I intend to add is the ability to control the software through keyboard shortcuts. Ideally, it would be usable without ever touching the mouse. These shortcuts could be set from the configuration file.

* A color picker might be added to lend less ambiguity to the process of determining colors in images. A number of colors would be specified in the configuration file, and upon mousing over or clicking a pixel in the image, the closest 'match' among these colors would be shown.

* Especially in the case of imagesets, I consider that the same sequence of tags might be frequently repeated between multiple images. This raises the question as to if it should be possible to copy tags from one image to another. If not directly implemented, a string containing all tags could be presented for copy-and-pasting.

* I've considered adding more features to the image-viewer itself, such as the ability to zoom, and the ability to display animation.

* Currently, the software produces little in the way of command-line output which could be logged. What is logged, is typically from within the wxPython library. Aside from the command-line logging, such information could also be included in a window or other widget, or flushed to a file.

* A scrollable menu of thumbnails for each image, which can be selected to change to a certain image might be handy for navigation. In the current state of the software, the user would need to remember the images by number, alone, to navigate to a specific one.

* At this point, the UI is a bit rough, in that there's not much empty space to separate or align the elements. That should definitely be added at some point. The 'sashes' which are dragged to resize the window panes are also a bit poorly defined. I can probably change that.

* The image is currently overlaid on a black background. If transparency is present, this might cause a measure of confusion to the user, so I will consider changing this to the standard alternating gray boxes pattern.

* Normally, the software periodically updates its output files, in case it suddenly crashes before its normal closing procedure would be done. Currently, this process runs in the background without any feedback to the user. I consider adding some kind of indication for it.
