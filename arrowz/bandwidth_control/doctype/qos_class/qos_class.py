# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class QoSClass(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		ceil_kbps: DF.Int
		class_name: DF.Data
		match_dscp: DF.Data | None
		match_ports: DF.Data | None
		match_protocol: DF.Literal["Any", "HTTP", "HTTPS", "DNS", "VoIP", "Gaming", "Streaming", "Custom"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		priority: DF.Int
		quantum: DF.Int
		rate_kbps: DF.Int
	# end: auto-generated types

	pass
