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


class saccade(item.item):

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
		self.item_type = "saccade"
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
			"Moving dot stimulus for saccadic eye movements"

		# The parent handles the rest of the contruction
		item.item.__init__(self, name, experiment, string)

	def prepare(self):

		"""
		Prepare the item. In this case this means drawing a fixation
		dot to an offline canvas.
		"""

		# create offline canvas
		self.canvas = canvas(self.experiment)
		self.canvas.set_bgcolor(self.get("bgc"))
		self.canvas.clear()

		# create keyboard object
		if self.allow_keyboard == 'yes':
			kl = self.get("kl").split(';')
			self.kb = keyboard(self.experiment, keylist=kl, timeout=None)

		# calculate stimulus radius
		self.r = self.get("stims")/2

		# define positions
		if self.get("direct") == "horizontal":
			self.positions = [
				(self.get("width")/2 - self.get("amp"), self.get("height")/2),
				(self.get("width")/2 + self.get("amp"), self.get("height")/2)
				]

		elif self.get("direct") == "vertical":
			self.positions = [
				(self.get("width")/2, self.get("height")/2 - self.get("amp")),
				(self.get("width")/2, self.get("height")/2 + self.get("amp"))
				]

		else:
			self.positions = [
				(self.get("width")/2, self.get("height")/2),
				(self.get("width")/2, self.get("height")/2)
				]
			print("Error in saccade.prepare: unkown direction!")

		# calculate vibration time (ms)
		self.experiment.set("T", (1 / float(self.get("freq"))) * 1000)
		
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
		key = None
		t0 = self.time()
		while self.time() - t0 < self.get("dur") and not key:
			for spos in self.positions:
				# update display
				self.canvas.clear()
				self.canvas.circle(spos[0],spos[1],self.r,fill=True,color=self.get("fgc"))
				# show display
				t1 = self.canvas.show()
				# timeout
				if self.get("dur") - (t1-t0) > self.get("T")/2:
					timeout = self.get("T")/2
				else:
					timeout = self.get("dur") - (t1-t0)
				# check for keypresses
				if self.allow_keyboard == 'yes':
					key, presstime = self.kb.get_key(timeout=max(1,timeout))
					if key:
						# set response variables
						self.experiment.set("response", key)
						self.experiment.set("response_time", presstime)
						break
				else:
					self.sleep(timeout=self.get("T")/2)

		# Report success
		return True

class qtsaccade(saccade, qtplugin.qtplugin):

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
		saccade.__init__(self, name, experiment, string)
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
		self.kl_line_edit_control = self.add_line_edit_control("kl", "Allowed keys", tooltip = \
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
		self.kl_line_edit_control.setDisabled(self.get("allow_keyboard") == 'no')
		self.lock = False
		return self._edit_widget
