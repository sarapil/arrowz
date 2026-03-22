# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BandwidthAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		arrowz_box: DF.Link
		bandwidth_plan: DF.Link
		client_group: DF.Link | None
		enabled: DF.Check
		lan_network: DF.Link | None
		network_client: DF.Link | None
		notes: DF.SmallText | None
		override_download_kbps: DF.Int
		override_upload_kbps: DF.Int
		priority: DF.Int
		target_type: DF.Literal["Client", "Group", "Network"]
		valid_from: DF.Datetime | None
		valid_until: DF.Datetime | None
	# end: auto-generated types

	def validate(self):
		self.validate_target()

	def validate_target(self):
		"""Ensure the correct target field is set based on target_type."""
		target_map = {
			"Client": "network_client",
			"Group": "client_group",
			"Network": "lan_network",
		}

		required_field = target_map.get(self.target_type)
		if required_field and not self.get(required_field):
			frappe.throw(
				_("Please set {0} for target type {1}.").format(
					frappe.bold(self.meta.get_label(required_field)),
					frappe.bold(self.target_type),
				)
			)

		# Clear unrelated target fields
		for target_type, field in target_map.items():
			if target_type != self.target_type:
				self.set(field, None)

	def on_update(self):
		self.push_tc_config()

	def push_tc_config(self):
		"""Push traffic control configuration to the Arrowz Box."""
		if not self.enabled:
			return

		frappe.publish_realtime(
			event="tc_config_update",
			message={
				"assignment": self.name,
				"arrowz_box": self.arrowz_box,
				"target_type": self.target_type,
				"bandwidth_plan": self.bandwidth_plan,
			},
			doctype="Arrowz Box",
			docname=self.arrowz_box,
		)
