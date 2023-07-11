from xml.dom.minidom import getDOMImplementation, parse
import gtk
import gtk.gdk
#from video import *
import os.path
import os
from PIL import Image
import getopt
import sys
import subprocess
#import trackerbase
from trackingresults import TrackingResults

from opencv.cv import *
from opencv.highgui import *

letters = 'i:v:o:w:f:n'
opts, extraparams = getopt.getopt(sys.argv[1:], letters)
#print "Options are:",opts
#print "Extra parameters are:",extraparams

imPath='default'
outputFile = 'detectedPoints.xml'
fbInfoFile = 'facebox.xml' # Filename of facebox info xml file
fbFile = 'fb.png'   # Filename of facebox image
verbose = 0
disp = 1    # - By default display images

pointNames = ["A", "A1", "B", "B1", "C", "D", "D1", "E", "E1", "F", "F1", "G", "G1", "H", "H1", "I", "J", "K", "L", "M"]

# -- Static face box filename
fbFname = '/tmp/fb.png'

for o,p in opts:
    if o in ['-i','--image']:
        imPath = p
    elif o in ['-o','--outputfile']:
        outputFile = p
    elif o in ['-v', '--verbose']:
        verbose = 1
    elif o == '-n':
        disp = 0
    elif o in ['-w', '--fbinfo']:
        fbInfoFile = p
    elif o in ['-f', '--facebox']:
        fbFile = p

#print 'Path of image:',imPath
#print 'Outputfile:', outputFile
#print 'Facebox image:', fbFile
#print 'Display = ', disp

def callPointDetector(target, cropx, cropy):
# TODO
#------
# 28082008 ==>  This function must be changed so that it takes the matlab compiled function instead of
#               actually calling matlab...

#IN:  target: [string] filename to save detected points
#     cropx: x position of top-left corner of facebox, relative to original image
#     cropy: y position of top-left corner of facebox, relative to original image
#OUT: void (saves points to file 'target')  
	print "Calling point detector"
	subprocess.call(['sliwiga_ffpd.exe', imPath, fbFile, target, str(cropx), str(cropy)])
    


def detectObject(image):
#IN:  image: cvImage object
#OUT: fboxDims: tuple of 4 ints: [left top right bot] of facebox

# -- Create empty grayscale object, of size image
	grayscale = cvCreateImage(cvSize(image.width, image.height), 8, 1)
	cvCvtColor(image, grayscale, CV_BGR2GRAY)
	storage = cvCreateMemStorage(0)
	cvClearMemStorage(storage)
	cvEqualizeHist(grayscale, grayscale)
	try:
		#cascade = cvLoadHaarClassifierCascade('data/facetracker/haarcascade_frontalface_alt2.xml', cvSize(1,1))
		cascade = cvLoadHaarClassifierCascade('data/haarcascade_frontalface_alt.xml', cvSize(1,1))
	except:
		print "Cannot find haarcascade file"
	# -- Something wrong with the following line. 'Throws' an int and terminate is called
	faces = cvHaarDetectObjects(grayscale, cascade, storage, 1.2, 2, CV_HAAR_DO_CANNY_PRUNING, cvSize(100,100))
	if faces:
		for i in faces:
			cvRectangle(image, cvPoint( int(i.x), int(i.y)), cvPoint(int(i.x+i.width), int(i.y+i.height)), CV_RGB(0,255,0), 3, 8, 0)
	else:
		print "No faces detected"

	# -- We want only one face: take facebox with max. area
	maxArea = 0
	fb = None
	if faces:
		for i in faces:
			area = i.width * i.height
			if area > maxArea:
				maxArea = area
				fb = i
	if fb == None:
		dialog = gtk.MessageDialog( None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "No face detected in image")
		dialog.run()
		dialog.destroy()
		return None
		
	hw = fb.width / 2
	hh = fb.height / 2

	ly = int(fb.y-hh) + fb.y * 1
	ly = min(ly, 479)

	h = int(ly - int(fb.y-hh))

	# -- Do this the hard way, using the python Image library, as I don't know
	#    how to crop cvImage objects
	img = Image.open(imPath) 
	fboxDims = (int(i.x), int(i.y),int(i.x+i.width), int(i.y+i.height))
	imgCropped = img.crop(fboxDims)
	imgCropped.save(fbFile, 'PNG')

	return fboxDims


def displayObject(image, name):
    cvNamedWindow(name, 1)
    cvShowImage(name, image)
    cvWaitKey(0)
    cvDestroyWindow(name)

def showPaintedPoints(fname, im):
# Reads detected points from XML and shows them in original image
#IN:  fname: .xresults filename
#     im: cvImage
        
	# -- Read the points
	R = TrackingResults()
	R.load(fname)
	# -- Paint the points
	pim = paintPoints(im, R)
	# -- Display image
	displayObject(pim, 'Detected points ('+fname+')')

def paintPoints(im, r):
# Paints points in an image (first frame)
#IN:  im: cvImage
#     r: TrackingResults object
#OUT: cvImage with points painted
        
	for i in pointNames:
		p = r.getResult(i, 0)   # - Always get from 1st frame
		print i+': x-position is %.2f and y-position is %.2f' %(p[0], p[1])
		# -- Now paint the image
		#roi = cvRect(int(p[0]), int(p[1]), 1, 1)
		#im.set_roi(roi, CV_RGB(0,255,0))
		cvCircle(im, cvPoint( int(p[0]), int(p[1])), 2, CV_RGB(0,255,0), 2)
	return im

def saveFaceboxInfo(fn, d):
	#"""Saves facebox info to file (XML)
	#IN: fn: filename
	#d: dimensions: [x_top y_left x_bot y_right]
	#OUT: none"""
	impl = getDOMImplementation()

	#create the results document
	fbDoc = impl.createDocument(None, "facebox-info", None)
	topElement = fbDoc.documentElement
	
	boxpointElement = fbDoc.createElement("boxpoint")
	boxpointElement.setAttribute("id", "topleft")
	boxpointElement.setAttribute("x", `d[0]`)
	boxpointElement.setAttribute("y", `d[1]`)

	topElement.appendChild(boxpointElement)

	boxpointElement = fbDoc.createElement("boxpoint")
	boxpointElement.setAttribute("id", "botright")
	boxpointElement.setAttribute("x", `d[2]`)
	boxpointElement.setAttribute("y", `d[3]`)

	topElement.appendChild(boxpointElement)
	text = fbDoc.toprettyxml()
	
	outFile = file(fn,"wt")
	outFile.write(text)
	outFile.close()
	
def main():
    # Read the image
	if os.path.isfile(imPath):
		image = cvLoadImage(imPath)
	else:
		print('Image not found')
		return
	#displayObject(image, 'Input image')
	ul = detectObject(image)
	#if disp:
	#	displayObject(image, 'Detected Face')
	#try:
	#	cvSaveImage(fbFname, image)
	#except:
	#	print "Failed to save facebox image"
	saveFaceboxInfo(fbInfoFile, ul)

    # -- Now detect the points in the facebox, using matlab
	callPointDetector(outputFile, ul[0], ul[1])
	if disp:
		showPaintedPoints(outputFile, image)

if __name__ == "__main__":
    main()