# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class QoSPolicy(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from arrowz.bandwidth_control.doctype.qos_class.qos_class import QoSClass

		arrowz_box: DF.Link
		classes: DF.Table[QoSClass]
		default_class: DF.Data | None
		description: DF.SmallText | None
		enabled: DF.Check
		policy_name: DF.Data
	# end: auto-generated types

	def validate(self):
		if not self.classes or len(self.classes) == 0:
			frappe.throw(_("QoS Policy must have at least one class defined."))
