# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

from frappe.model.document import Document


class ArrowzBoxHealthLog(Document):
	"""Log entry for Arrowz Box health events.

	These records are created automatically by telemetry sync,
	heartbeat checks, and engine events. They are append-only.
	"""

	pass
