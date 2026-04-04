# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

from frappe.model.document import Document


class BandwidthPlanTier(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		burst_download_kbps: DF.Int
		burst_upload_kbps: DF.Int
		description: DF.SmallText | None
		download_kbps: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		priority: DF.Int
		tier_name: DF.Data
		upload_kbps: DF.Int
	# end: auto-generated types

	pass
