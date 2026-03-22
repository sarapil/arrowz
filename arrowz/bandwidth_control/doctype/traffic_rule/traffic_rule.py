# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TrafficRule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action: DF.Literal["Mark", "Shape", "Limit", "Accept"]
		action_value: DF.Data | None
		arrowz_box: DF.Link
		bandwidth_plan: DF.Link | None
		comment: DF.SmallText | None
		enabled: DF.Check
		match_destination: DF.Data | None
		match_dscp: DF.Data | None
		match_port: DF.Data | None
		match_protocol: DF.Literal["Any", "TCP", "UDP", "ICMP"]
		match_source: DF.Data | None
		priority: DF.Int
		rule_name: DF.Data
	# end: auto-generated types

	def validate(self):
		if self.action in ("Mark", "Shape", "Limit") and not self.action_value:
			frappe.throw(
				_("Action Value is required when action is {0}.").format(
					frappe.bold(self.action)
				)
			)

		if self.action == "Shape" and not self.bandwidth_plan:
			frappe.throw(_("Bandwidth Plan is required when action is Shape."))

	def on_update(self):
		self.push_config()

	def push_config(self):
		"""Push traffic rule configuration to the Arrowz Box."""
		frappe.publish_realtime(
			event="traffic_rule_update",
			message={
				"rule": self.name,
				"arrowz_box": self.arrowz_box,
				"action": self.action,
				"enabled": self.enabled,
			},
			doctype="Arrowz Box",
			docname=self.arrowz_box,
		)
