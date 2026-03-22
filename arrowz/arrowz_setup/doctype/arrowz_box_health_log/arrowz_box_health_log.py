# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ArrowzBoxHealthLog(Document):
	"""Log entry for Arrowz Box health events.

	These records are created automatically by telemetry sync,
	heartbeat checks, and engine events. They are append-only.
	"""

	pass
