# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class ClientSession(Document):
	def validate(self):
		self.calculate_duration()

	def calculate_duration(self):
		"""Calculate duration in seconds if end_time exists."""
		if self.end_time and self.start_time:
			self.duration_seconds = int(time_diff_in_seconds(self.end_time, self.start_time))
