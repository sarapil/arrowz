# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Input validators for Arrowz network configuration fields.

Provides reusable validation functions for IP addresses, CIDRs,
MAC addresses, ports, hostnames, and other network-related inputs.
"""

import ipaddress
import re

import frappe
from frappe import _


# ── Compiled Patterns ────────────────────────────────────────────────

MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")
HOSTNAME_PATTERN = re.compile(
	r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
)
PORT_RANGE_PATTERN = re.compile(r"^\d+(-\d+)?$")
SSID_PATTERN = re.compile(r"^[\x20-\x7E]{1,32}$")


# ── IP Address ───────────────────────────────────────────────────────

def validate_ip(value: str, field_label: str = "IP Address") -> str:
	"""Validate an IPv4 or IPv6 address.

	Args:
		value: IP address string
		field_label: Field label for error messages

	Returns:
		Normalized IP address string

	Raises:
		frappe.ValidationError on invalid input
	"""
	if not value:
		return value
	try:
		addr = ipaddress.ip_address(value.strip())
		return str(addr)
	except ValueError:
		frappe.throw(
			_("{0} is not a valid IP address: {1}").format(field_label, value),
			frappe.ValidationError,
		)


def validate_cidr(value: str, field_label: str = "CIDR") -> str:
	"""Validate a CIDR notation network address.

	Args:
		value: CIDR string (e.g., "192.168.1.0/24")
		field_label: Field label for error messages

	Returns:
		Normalized CIDR string

	Raises:
		frappe.ValidationError on invalid input
	"""
	if not value:
		return value
	try:
		network = ipaddress.ip_network(value.strip(), strict=False)
		return str(network)
	except ValueError:
		frappe.throw(
			_("{0} is not a valid CIDR: {1}").format(field_label, value),
			frappe.ValidationError,
		)


def validate_subnet_mask(value: str, field_label: str = "Subnet Mask") -> str:
	"""Validate a subnet mask.

	Args:
		value: Subnet mask string (e.g., "255.255.255.0")
		field_label: Field label for error messages

	Returns:
		Validated subnet mask string
	"""
	if not value:
		return value

	valid_masks = {
		"255.255.255.255", "255.255.255.254", "255.255.255.252",
		"255.255.255.248", "255.255.255.240", "255.255.255.224",
		"255.255.255.192", "255.255.255.128", "255.255.255.0",
		"255.255.254.0", "255.255.252.0", "255.255.248.0",
		"255.255.240.0", "255.255.224.0", "255.255.192.0",
		"255.255.128.0", "255.255.0.0", "255.254.0.0",
		"255.252.0.0", "255.248.0.0", "255.240.0.0",
		"255.224.0.0", "255.192.0.0", "255.128.0.0",
		"255.0.0.0", "254.0.0.0", "252.0.0.0",
		"248.0.0.0", "240.0.0.0", "224.0.0.0",
		"192.0.0.0", "128.0.0.0", "0.0.0.0",
	}

	if value.strip() not in valid_masks:
		frappe.throw(
			_("{0} is not a valid subnet mask: {1}").format(field_label, value),
			frappe.ValidationError,
		)

	return value.strip()


def validate_ip_in_subnet(ip: str, network_ip: str, subnet_mask: str, field_label: str = "IP") -> bool:
	"""Check if an IP address belongs to a subnet.

	Args:
		ip: IP address to check
		network_ip: Network gateway IP
		subnet_mask: Subnet mask

	Returns:
		True if IP is in the subnet
	"""
	try:
		prefix_len = ipaddress.IPv4Network(f"0.0.0.0/{subnet_mask}").prefixlen
		network = ipaddress.IPv4Network(f"{network_ip}/{prefix_len}", strict=False)
		return ipaddress.IPv4Address(ip) in network
	except ValueError:
		return False


# ── MAC Address ──────────────────────────────────────────────────────

def validate_mac(value: str, field_label: str = "MAC Address") -> str:
	"""Validate and normalize a MAC address.

	Args:
		value: MAC address string
		field_label: Field label for error messages

	Returns:
		Uppercase colon-separated MAC (XX:XX:XX:XX:XX:XX)
	"""
	if not value:
		return value

	# Normalize separators
	cleaned = value.strip().upper().replace("-", ":").replace(".", "")

	# Handle Cisco format (xxxx.xxxx.xxxx)
	if len(cleaned) == 12 and ":" not in cleaned:
		cleaned = ":".join(cleaned[i : i + 2] for i in range(0, 12, 2))

	if not MAC_PATTERN.match(cleaned):
		frappe.throw(
			_("{0} is not a valid MAC address: {1}").format(field_label, value),
			frappe.ValidationError,
		)

	return cleaned


# ── Port ─────────────────────────────────────────────────────────────

def validate_port(value, field_label: str = "Port") -> int:
	"""Validate a port number.

	Args:
		value: Port number (int or string)
		field_label: Field label for error messages

	Returns:
		Validated port as integer
	"""
	if value is None:
		return value
	try:
		port = int(value)
	except (ValueError, TypeError):
		frappe.throw(
			_("{0} must be a number: {1}").format(field_label, value),
			frappe.ValidationError,
		)
		return None

	if not (1 <= port <= 65535):
		frappe.throw(
			_("{0} must be between 1 and 65535: {1}").format(field_label, port),
			frappe.ValidationError,
		)

	return port


def validate_port_range(value: str, field_label: str = "Port Range") -> str:
	"""Validate a port or port range string.

	Accepts: "80", "8080-8090", "80,443,8080"

	Args:
		value: Port range string
		field_label: Field label for error messages

	Returns:
		Validated port range string
	"""
	if not value:
		return value

	parts = value.strip().split(",")
	for part in parts:
		part = part.strip()
		if not PORT_RANGE_PATTERN.match(part):
			frappe.throw(
				_("{0} has invalid format: {1}").format(field_label, part),
				frappe.ValidationError,
			)
		if "-" in part:
			start, end = part.split("-")
			if not (1 <= int(start) <= 65535 and 1 <= int(end) <= 65535):
				frappe.throw(
					_("{0} port out of range: {1}").format(field_label, part),
					frappe.ValidationError,
				)
			if int(start) >= int(end):
				frappe.throw(
					_("{0} start must be less than end: {1}").format(field_label, part),
					frappe.ValidationError,
				)
		else:
			validate_port(part, field_label)

	return value.strip()


# ── Hostname ─────────────────────────────────────────────────────────

def validate_hostname(value: str, field_label: str = "Hostname") -> str:
	"""Validate a hostname or FQDN.

	Args:
		value: Hostname string
		field_label: Field label for error messages

	Returns:
		Lowercase validated hostname
	"""
	if not value:
		return value

	cleaned = value.strip().lower()
	if len(cleaned) > 253:
		frappe.throw(
			_("{0} is too long (max 253 characters)").format(field_label),
			frappe.ValidationError,
		)

	if not HOSTNAME_PATTERN.match(cleaned):
		frappe.throw(
			_("{0} is not a valid hostname: {1}").format(field_label, value),
			frappe.ValidationError,
		)

	return cleaned


# ── SSID ─────────────────────────────────────────────────────────────

def validate_ssid(value: str, field_label: str = "SSID") -> str:
	"""Validate a WiFi SSID.

	Args:
		value: SSID string (1-32 printable ASCII characters)
		field_label: Field label for error messages

	Returns:
		Validated SSID string
	"""
	if not value:
		return value

	if len(value) > 32:
		frappe.throw(
			_("{0} must be 32 characters or fewer").format(field_label),
			frappe.ValidationError,
		)

	if not SSID_PATTERN.match(value):
		frappe.throw(
			_("{0} contains invalid characters").format(field_label),
			frappe.ValidationError,
		)

	return value


# ── VLAN ─────────────────────────────────────────────────────────────

def validate_vlan_id(value, field_label: str = "VLAN ID") -> int:
	"""Validate a VLAN ID.

	Args:
		value: VLAN ID (1-4094)
		field_label: Field label for error messages

	Returns:
		Validated VLAN ID as integer
	"""
	if value is None or value == 0:
		return value

	try:
		vlan = int(value)
	except (ValueError, TypeError):
		frappe.throw(
			_("{0} must be a number").format(field_label),
			frappe.ValidationError,
		)
		return None

	if not (1 <= vlan <= 4094):
		frappe.throw(
			_("{0} must be between 1 and 4094").format(field_label),
			frappe.ValidationError,
		)

	return vlan


# ── MTU ──────────────────────────────────────────────────────────────

def validate_mtu(value, field_label: str = "MTU") -> int:
	"""Validate an MTU value.

	Args:
		value: MTU value (68-9000)
		field_label: Field label for error messages

	Returns:
		Validated MTU as integer
	"""
	if value is None:
		return value

	try:
		mtu = int(value)
	except (ValueError, TypeError):
		frappe.throw(
			_("{0} must be a number").format(field_label),
			frappe.ValidationError,
		)
		return None

	if not (68 <= mtu <= 9000):
		frappe.throw(
			_("{0} must be between 68 and 9000").format(field_label),
			frappe.ValidationError,
		)

	return mtu
