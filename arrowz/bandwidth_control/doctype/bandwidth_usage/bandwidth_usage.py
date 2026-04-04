# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

from frappe.model.document import Document


class BandwidthUsage(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		arrowz_box: DF.Link
		average_download_kbps: DF.Float
		average_upload_kbps: DF.Float
		bytes_downloaded: DF.Int
		bytes_uploaded: DF.Int
		client_group: DF.Link | None
		network_client: DF.Link | None
		packets_downloaded: DF.Int
		packets_uploaded: DF.Int
		peak_download_kbps: DF.Float
		peak_upload_kbps: DF.Float
		period_type: DF.Literal["5min", "Hourly", "Daily", "Monthly"]
		timestamp: DF.Datetime
	# end: auto-generated types

	pass
