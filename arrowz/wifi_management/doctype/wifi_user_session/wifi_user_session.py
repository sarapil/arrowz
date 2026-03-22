# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class WiFiUserSession(Document):
	def validate(self):
		self.calculate_duration()

	def calculate_duration(self):
		"""Calculate session duration if both start and end time are set."""
		if self.start_time and self.end_time:
			duration = time_diff_in_seconds(self.end_time, self.start_time)
			if duration < 0:
				import frappe
				frappe.throw(frappe._("End Time cannot be before Start Time"))
