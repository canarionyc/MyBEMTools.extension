#! ipy3
# -*- coding: utf-8 -*-
import os
import time
from pyrevit import HOST_APP, DB

# 1. SETUP INTERNAL LOGGING
log_path = r"C:\RevitAudit\headless_debug_log.txt"


def write_to_log(message):
	with open(log_path, "a") as f:
		f.write("[{}] {}\n".format(time.strftime("%H:%M:%S"), message))


# 2. THE MAIN EXECUTION
try:
	write_to_log("--- SCRIPT STARTING ---")

	# Wait up to 10 seconds for the document to become available
	doc = None
	for i in range(15):
		doc = HOST_APP.doc
		if doc:
			break
		write_to_log("Waiting for model to load... (Attempt {})".format(i + 1))
		time.sleep(1)

	if doc:
		write_to_log("SUCCESS: Document detected: " + doc.Title)

		# Count Walls as a stability test
		walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements()
		write_to_log("Audit complete. Total walls found: " + str(len(walls)))
	else:
		write_to_log("ERROR: Revit opened but the model never became active.")

except Exception as e:
	write_to_log("CRASH: " + str(e))

write_to_log("--- SCRIPT FINISHED ---")