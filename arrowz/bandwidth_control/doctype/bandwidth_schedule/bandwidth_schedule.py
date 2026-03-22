# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BandwidthSchedule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from arrowz.bandwidth_control.doctype.bandwidth_schedule_slot.bandwidth_schedule_slot import BandwidthScheduleSlot

		arrowz_box: DF.Link | None
		description: DF.SmallText | None
		enabled: DF.Check
		fallback_plan: DF.Link | None
		schedule_name: DF.Data
		slots: DF.Table[BandwidthScheduleSlot]
	# end: auto-generated types

	def validate(self):
		self.validate_no_overlapping_slots()

	def validate_no_overlapping_slots(self):
		"""Ensure no two slots overlap on the same day."""
		if not self.slots:
			return

		slots_by_day: dict[str, list] = {}
		for slot in self.slots:
			days = []
			if slot.day_of_week == "All":
				days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
			else:
				days = [slot.day_of_week]

			for day in days:
				slots_by_day.setdefault(day, [])
				slots_by_day[day].append(slot)

		for day, day_slots in slots_by_day.items():
			# Sort by start_time
			sorted_slots = sorted(day_slots, key=lambda s: str(s.start_time))
			for i in range(len(sorted_slots) - 1):
				current = sorted_slots[i]
				next_slot = sorted_slots[i + 1]
				if str(current.end_time) > str(next_slot.start_time):
					frappe.throw(
						_("Time slots overlap on {0}: {1}-{2} and {3}-{4}").format(
							frappe.bold(day),
							current.start_time,
							current.end_time,
							next_slot.start_time,
							next_slot.end_time,
						)
					)
