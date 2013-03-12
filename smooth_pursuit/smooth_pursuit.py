"""
Author: Edwin Dalmaijer
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

from libopensesame import item, exceptions
from libqtopensesame import qtplugin
from openexp.canvas import canvas
from openexp.keyboard import keyboard
from PyQt4 import QtGui, QtCore

import math


class smooth_pursuit(item.item):

	"""
	This class (the class with the same name as the module)
	handles the basic functionality of the item. It does
	not deal with GUI stuff.
	"""

	def __init__(self, name, experiment, string=None):

		"""
		Constructor

		Arguments:
		name -- name of the item
		experiment -- the experiment

		Keyword arguments
		string -- definitional string (default = None)
		"""

		# The item_type should match the name of the module
		self.item_type = "smooth_pursuit"
		self.mtype = "sinusoid"
		self.direct = "horizontal"
		self.dur = 5000
		self.freq = 1
		self.amp = 100
		self.fgc = experiment.foreground
		self.bgc = experiment.background
		self.stims = 8
		self.allow_keyboard = 'no'
		self.kl = ""

		# Provide a short accurate description of the items functionality
		self.description = \
			"Moving dot stimulus for smooth pursuit eye movements"

		# The parent handles the rest of the contruction
		item.item.__init__(self, name, experiment, string)

	def no_change(self,amp,T,time):

		"""
		Calculates nothing, just returns 0.
		"""

		return 0

	def linear(self,amp,T,time):

		"""
		Calculates the current value considering given amplitude,
		vribration time (T) and time on a linear slope.
		FUNCTION REQUIRES FLOATS!
		"""

		if ((time % T)/T) <= 0.5:
			return amp * (4*((time % T)/T) - 1)
		elif ((time % T)/T) > 0.5:
			return amp * (-4*((time % T)/T) + 3)

	def sinusoid(self,amp,T,time):

		"""
		Calculates the current value considering given amplitude,
		vribration time (T) and time on a sinusoid.
		FUNCTION REQUIRES FLOATS!
		"""

		return amp * math.sin(((time % T)/T) * 2 * math.pi)

	def prepare(self):

		"""
		Prepare the item. In this case this means drawing a fixation
		dot to an offline canvas.
		"""

		# create offline canvas
		self.canvas = canvas(self.experiment)
		self.canvas.set_bgcolor(self.get("bgc"))
		self.canvas.clear()

		# draw the stimulus
		self.sx = self.get("width")/2
		self.sy = self.get("height")/2
		self.r = self.get("stims")/2
		self.canvas.circle(self.sx,self.sy,self.r,fill=True,color=self.get("fgc"))

		# create keyboard object
		if self.allow_keyboard == 'yes':
			kl = self.get("kl").split(';')
			self.kb = keyboard(self.experiment, keylist=kl, timeout=None)

		# calculate vibration time (ms)
		self.experiment.set("T", (1 / float(self.get("freq"))) * 1000)

		# determine functions for stepsize
		if self.get("direct") == 'horizontal':
			if self.get("mtype") == 'sinusoid':
				self.fx = self.sinusoid
			elif self.get("mtype") == 'linear':
				self.fx = self.linear
			else:
				self.fx = self.no_change
				print("Error in smooth_pursuit.prepare: unknown movement type!")
			self.fy = self.no_change

		elif self.get("direct") == 'vertical':
			if self.mtype == 'sinusoid':
				self.fy = self.sinusoid
			elif self.mtype == 'linear':
				self.fy = self.linear
			else:
				self.fy = self.no_change
				print("Error in smooth_pursuit.prepare: unknown movement type!")
			self.fx = self.no_change
		
		# Pass the word on to the parent
		item.item.prepare(self)

		# Report success
		return True

	def run(self):

		"""
		Run the item. In this case this means putting the offline canvas
		to the display and waiting for the specified duration.
		"""

		self.set_item_onset()

		# run until timeout (or keypress)
		t0 = self.time()
		while self.time() - t0 < self.get("dur"):
			# show display
			self.canvas.show()
			# update display
			x = self.sx - self.fx(float(self.get("amp")),float(self.get("T")),self.time())
			y = self.sy - self.fy(float(self.get("amp")),float(self.get("T")),self.time())
			self.canvas.clear()
			self.canvas.circle(x,y,self.r,fill=True,color=self.get("fgc"))
			# check for keypresses
			if self.allow_keyboard == 'yes':
				key, presstime = self.kb.get_key(timeout=1)
				if key:
					# set response variables
					self.experiment.set("response", key)
					self.experiment.set("response_time", presstime)
					break

		# Report success
		return True

class qtsmooth_pursuit(smooth_pursuit, qtplugin.qtplugin):

	"""
	This class (the class named qt[name of module] handles
	the GUI part of the plugin. For more information about
	GUI programming using PyQt4, see:
	<http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/classes.html>
	"""

	def __init__(self, name, experiment, string = None):

		"""
		Constructor
		"""

		# Pass the word on to the parents
		smooth_pursuit.__init__(self, name, experiment, string)
		qtplugin.qtplugin.__init__(self, __file__)

	def init_edit_widget(self):

		"""
		This function creates the controls for the edit
		widget.
		"""

		# Lock the widget until we're done creating it
		self.lock = True

		# Pass the word on to the parent
		qtplugin.qtplugin.init_edit_widget(self, False)

		# content
		self.add_combobox_control("mtype", "Movement type", \
			["sinusoid","linear"], tooltip = "Type of stimulus movement")
		self.add_combobox_control("direct", "Movement direction", \
			["horizontal","vertical"], tooltip = "Direction of the stimulus movement")
		self.add_line_edit_control("dur", "Duration", \
			tooltip = "Duration in milliseconds (or 'infinite'; only use that when keyboard is allowed!)")
		self.add_line_edit_control("freq", "Movement frequency", \
			tooltip = "The movement frequency (in Hertz)")
		self.add_line_edit_control("amp", "Movement amplitude", \
			tooltip = "The amplitude of the stimulus' movement (in pixels)")
		self.add_color_edit_control("fgc", "Stimulus colour", \
			tooltip = "Expecting a colourname (e.g., 'blue') or an HTML colour (e.g., '#0000FF')")
		self.add_color_edit_control("bgc", "Background colour", \
			tooltip = "Expecting a colourname (e.g., 'blue') or an HTML colour (e.g., '#0000FF')")
		self.add_spinbox_control("stims", "Stimulus size", 0, 1000, \
			tooltip = "The diameter of the stimulus")
		self.add_checkbox_control('allow_keyboard', \
			'Allow keyboard response', tooltip= \
			'Set to allow a participant to use the keyboard')
		self.add_line_edit_control("kl", "Allowed keys", tooltip = \
			"Names of keys participants are allowed to press, seperated by a semicolon (e.g. 'right;left')")

		# Unlock
		self.lock = False

	def apply_edit_changes(self):

		"""Apply the controls"""

		if not qtplugin.qtplugin.apply_edit_changes(self, False) or self.lock:
			return
		self.experiment.main_window.refresh(self.name)

	def edit_widget(self):

		"""Update the controls"""

		self.lock = True
		qtplugin.qtplugin.edit_widget(self)
		self.lock = False
		return self._edit_widget
