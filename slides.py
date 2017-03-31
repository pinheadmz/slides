#!/usr/bin/sudo python

################
# dependencies #
################

import atexit
import curses
import time
import os
import json
import random
import sys
from subprocess import Popen, PIPE, STDOUT
from PIL import Image, ImageDraw, ImageFont

from datetime import datetime
from rgbmatrix import Adafruit_RGBmatrix


#############
# constants #
#############

# this directory
rootdir = sys.path[0]

# test file
imgfile = ( rootdir + '/cat-icon.png')

# starting image coordinates
IMGX = 0
IMGY = 0
IMGWIDTH = 0
IMGHEIGHT = 0

# load font
font = ImageFont.load_path( rootdir + '/fonts/pilfonts/timR08.pil')

# refresh rate in seconds
REFRESH = 1

# flag to "mute" LED grid
LEDGRID = True

# rotate grid output: 0, 90, 180, 270
ROTATE = 90

##############
# initialize #
##############

# runs on script exit, resets terminal settings
def cleanup():
	# undo curses settings
	curses.nocbreak()
	curses.echo()
	curses.endwin()
	
	matrix.Clear()
	print "bye!"
atexit.register(cleanup)

# init curses for text output and getch()
stdscr = curses.initscr()
stdscr.keypad(True) 		# arrow keys
curses.start_color()
curses.noecho()
curses.halfdelay(REFRESH * 10) 	# reset with nocbreak, blocking value is x 0.1 seconds

# store window dimensions
MAXYX = stdscr.getmaxyx()

# some terminals don't like invisible cursors
try:
	curses.curs_set(0)
	invisCursor = True
except curses.error:
	invisCursor = False

# color pairs for curses, keeping all colors < 8 for dumb terminals
COLOR_GOLD = 1
curses.init_pair(COLOR_GOLD, 3, 0)
COLOR_LTBLUE = 7
curses.init_pair(COLOR_LTBLUE, 6, 0)
COLOR_GREEN = 2
curses.init_pair(COLOR_GREEN, 2, 0)
COLOR_WHITE = 3
curses.init_pair(COLOR_WHITE, 7, 0)
COLOR_RED = 6
curses.init_pair(COLOR_RED, 1, 0)
COLOR_PINK = 5
curses.init_pair(COLOR_PINK, 5, 0)
COLOR_BLUE = 4
curses.init_pair(COLOR_BLUE, 4, 0)

# init LED grid, rows and chain length are both required parameters:
matrix = Adafruit_RGBmatrix(32, 1)


#############
# functions #
#############

# load image file
def loadImage(imagefile):
	global IMGX, IMGY, IMGWIDTH, IMGHEIGHT
	img = Image.open(imagefile)
	pixels = img.load()
	IMGWIDTH = img.size[0]
	IMGHEIGHT = img.size[1]
	return (pixels, img)
	
# draw 32 x 32 of pixels from image to LED grid - ignore alpha
def drawArea(img, imgx, imgy):
	for x in range(32):
		for y in range(32):
			bufferPixel(x, y, *img[imgx+x, imgy+y][:3])

# fill buffer matrix with black (off) pixels
def bufferInit():
	global buffer
	buffer = [[(0,0,0) for i in range(32)] for j in range(32)]

# change a pixel in the buffer
def bufferPixel(x, y, r, g, b):
	global buffer
	buffer[x][y] = (r, g, b)
	
# draw entire buffer to LED grid without needing clear()
def bufferDraw():
	for x in range(32):
		for y in range(32):
			if ROTATE == 0:
				matrix.SetPixel(x, y, *buffer[x][y])
			elif ROTATE == 90:
				matrix.SetPixel(x, y, *buffer[y][31-x])
			elif ROTATE == 180:
				matrix.SetPixel(x, y, *buffer[31-x][31-y])
			elif ROTATE == 270:
				matrix.SetPixel(x, y, *buffer[31-y][x])
			
# stash cursor in the bottom right corner in case terminal won't invisiblize it
def hideCursor():
	stdscr.addstr(MAXYX[0]-1, MAXYX[1]-1, "")

# check for keyboard input -- also serves as the pause between REFRESH cycles
def checkKeyIn():
	global IMGX, IMGY, IMGWIDTH, IMGHEIGHT
	keyNum = stdscr.getch()
	
	if keyNum == curses.KEY_RIGHT:
		if IMGX + 32 < IMGWIDTH:
			IMGX += 1
	elif keyNum == curses.KEY_LEFT:
		if IMGX > 0:
			IMGX -= 1
	elif keyNum == curses.KEY_DOWN:
		if IMGY + 32 < IMGHEIGHT:
			IMGY += 1
	elif keyNum == curses.KEY_UP:
		if IMGY > 0:
			IMGY -= 1
	elif 0 <= keyNum <= 255:
		key = chr(keyNum)
		if key in ("q", "Q"):
			sys.exit()
		elif key in ("l", "L"):
			global LEDGRID
			LEDGRID = not LEDGRID

# use curses to output a line (or two) of text towards bottom of the screen
def printMsg(msg, color=COLOR_WHITE, line=0):
	stdscr.erase()
	stdscr.addstr(2 + line, 0, msg, curses.color_pair(color))
	hideCursor()
	stdscr.refresh()

# fun random color glittery mayhem party!
def party(loops):
	# celebrate!
	for x in range(loops):
		# color splatter
		for y in range(400):
			pix = (random.randint(0,31), random.randint(0,31), random.randint(0,255), random.randint(0,255), random.randint(0,255))
			matrix.SetPixel(*pix)
			time.sleep(.001)
		# clear a few holes
		for i in range(1000):
			matrix.SetPixel (random.randint(0,31), random.randint(0,31),0,0,0)
			time.sleep(.0005)

#####################
### THE MAIN LOOP! ##
#####################

(imagePixels, img) = loadImage(imgfile)
process = Popen(['fbi','-a',imgfile])

while True:		
	#############################
	# BEGIN DRAWING TO LED GRID #
	#############################
	#clear buffer
	bufferInit()

	if LEDGRID:
		drawArea(imagePixels, IMGX, IMGY)
	
	# push buffer to actual LED grid
	bufferDraw()

	######################################
	# PRINT ADDITIONAL OUTPUT TO CONSOLE #
	######################################

	# console is 94x28
	#stdscr.erase()

	# display image on terminal
	#img.show()

	#menu = "[Q]uit  [L]ED Grid"
	#stdscr.addstr(MAXYX[0]-1, 0, menu)
	
	# if cursor is visible get it out of the way
	#hideCursor()

	# push text buffer to terminal display
	#stdscr.refresh()
	
	# check for keyboard input and pause before display refresh
	checkKeyIn()
