# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class BandwidthPlan(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from arrowz.bandwidth_control.doctype.bandwidth_plan_tier.bandwidth_plan_tier import BandwidthPlanTier

		billing_plan: DF.Link | None
		burst_download_kbps: DF.Int
		burst_duration_seconds: DF.Int
		burst_upload_kbps: DF.Int
		description: DF.SmallText | None
		download_kbps: DF.Int
		enabled: DF.Check
		plan_name: DF.Data
		qos_policy: DF.Link | None
		tiers: DF.Table[BandwidthPlanTier]
		upload_kbps: DF.Int
	# end: auto-generated types

	def validate(self):
		if self.download_kbps <= 0:
			frappe.throw(_("Download Speed (Kbps) must be greater than 0."))
		if self.upload_kbps <= 0:
			frappe.throw(_("Upload Speed (Kbps) must be greater than 0."))

		if self.burst_download_kbps and self.burst_download_kbps < self.download_kbps:
			frappe.throw(_("Burst Download speed cannot be less than the base Download speed."))
		if self.burst_upload_kbps and self.burst_upload_kbps < self.upload_kbps:
			frappe.throw(_("Burst Upload speed cannot be less than the base Upload speed."))
