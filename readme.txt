**************************************************************************************************
					About SurvivalTracker
**************************************************************************************************

SurvivalTracker was developped by Lucas Kinsey (2024). The purpose of survival tracker is to be 
able to annotate biological images taken over the course of several time points with time in between 
each measurement with the motivation to create ground truth datasets that are easy to interpret in 
downstream pipelines. This is supposed to be a simple UI that is intuitive to use, fast, and could 
even be used to educate on the some cool applications of PyQt6. 

Included in this repo is a demo dataset of EGFP expressed in V1 layer 2/3 dendrites, zoomed in to 
depict dendritic spines. For more info about these images and how they were taken, please contact me :) 

A good demo to understand how this works is to label the spines on each time point from the demo dataset 
and generate labels for each region of interest (roi). I think learning is best done through examples, 
hopefully by running through the demo together a functioning intuition can be gained. If this tool
could be useful for someone's annotation project, feel free to use this, modify this, and take from 
it what you want :)
**************************************************************************************************

				Using the UI --  Workflow

**************************************************************************************************

/SurvivalTracker/UI/scripts/spineTracker.py is used to track longitudinal annotations of biological
measurements. 

Left clicking on any point in an image places a polygon at that location. 
On the first frame, place all desired polygons. 
To save your selections at this time point, press the space bar or click the "verify labels" button at bottom.
use arrow buttons, or "d", to travel to next image in time (or "a" to go back to previous image).
To carry over previous labels (useful for well aligned images) -- press "w".
to reset your current frame labeling, press "r".
If you are satisfied with all labels on all time points of this roi, press enter. (this will create a 
	/labels/ path in the mouseID folder in your data. It contains a JSON of all your labels over time)
Pressing enter will reset the drop down menu index, but labeled rois will display a check mark next to their
name, while unlabelled roi's will display an x by their name. mouseIDs that have labels (not necessarily complete),
will have a check mark. mouseIDs that do not have any labels yet will have x marks by their names.

and thats it. run the python script (should be executable in a .bat file, so no-code needed for annotating).
**************************************************************************************************

			Preprocess Experiment Summaries (optional - requires MATLAB)
- requires this too: 
https://www.mathworks.com/matlabcentral/fileexchange/10867-uipickfiles-uigetfile-on-steroids

			Optional demo in "'/SurvivalTracker/demo/withPreprocessing'" folder, 
			default demo uses "'/SurvivalTracker/demo/withoutPreprocessing'"

**************************************************************************************************

This section is optional. But to understand how the images are able to be viewed in the UI, it might
be helpful to briefly skim this. This is optional because there are probably better ways to get the data
prepared for visualization in the UI. 

TL;DR --> the images you annotate come from a tiff stack of "pseudo-registered" images found in the "data" folder in this repo.
		in order to flip through images to track annotations over time, images need to be in a tiff stack, where
		each page is a seperate time point.

	*** Note: the file structure of the data needs to match this "mouseID-->date-->roiNum#.tif" format, this is how the UI
		detects completion and availability of rois to annotate.

Data is stored in this structure:

--data
  --mouseID
	->date1
		--> scan1
		--> scan2
		--> scan3
		--> info.csv
	->date2
		--> scan1
		--> scan2
		--> scan3
		--> info.csv
	->date3
		--> scan1
		--> scan2
		--> scan3
		--> info.csv
	ect...

  --mouseID
	->date1
		--> scan1
		--> scan2
		--> scan3
		--> scan4
		--> scan5
		--> info.csv

	ect...

what preprocessing does is it iterates through each date for a mouse (each date is a "measurement")
and extracts an roi from each measurement so that it can concatenate it into an "aligned" stack. It uses 
the "info.csv" to get organize what order to iterate through the scans and how to make sure scans are being put
in the correct scan stack. the output is a bunch of stacks titled "roiNum#.tif" in each mouseID folder. There
is probably a better way to do this, but this is how the demo does it, and so if you are interested
you can run the matlab demo in the "withpreprocessing" folder of this repo. When selecting files, select files


not all preprocessed ROIs are aligned well. Manual quality control of preprocessed ROI labels may be necessary.
withoutpreprocessing demo already is quality controlled.

