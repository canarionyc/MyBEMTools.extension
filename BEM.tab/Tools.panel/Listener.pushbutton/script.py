# -*- coding: utf-8 -*-
import sys
import codecs

# --- ENCODING GUARD: Fixes codepage___0 error ---
try:
    if not sys.stdout.encoding or '0' in str(sys.stdout.encoding):
        # Force the output to use a valid UTF-8 writer
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr)
except Exception:
    pass

# --- ASSEMBLY GUARD: Fixes version conflict (25.0 vs 25.4) ---
import clr
try:
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI")
except Exception as e:
    # This identifies if the loader failed due to the 25.4 conflict
    pass

import os
import sys
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import clr

# 1. Revit API Imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent

from pyrevit import forms, script

# --- CONFIGURATION ---
PORT = 8080
OUTPUT_LOG = r"C:\Users\Public\bem_audit_log.json"


# --- THE WORKER (Main Thread) ---
class AuditHandler(IExternalEventHandler):
	"""This class executes the actual BIM logic inside the Revit main thread."""

	def __init__(self):
		self.data_packet = None

	def Execute(self, app):
		try:
			# Access the live document
			ui_doc = app.ActiveUIDocument
			if not ui_doc:
				return
			doc = ui_doc.Document

			# Example BIM Logic: Get counts of critical BEM elements
			walls = FilteredElementCollector(doc).OfClass(Wall).GetElementCount()
			floors = FilteredElementCollector(doc).OfClass(Floor).GetElementCount()

			result = {
				"status": "success",
				"model": doc.Title,
				"data": {
					"walls": walls,
					"floors": floors,
				},
				"client_msg": self.data_packet.get("message", "No message")
			}

			with open(OUTPUT_LOG, "w") as f:
				json.dump(result, f, indent=4)

			print("Audit completed for: {}".format(doc.Title))

		except Exception as e:
			with open(OUTPUT_LOG, "w") as f:
				json.dump({"status": "error", "error": str(e)}, f)

	def GetName(self):
		return "MyBEMTools_Listener_Handler"


# --- GLOBALS FOR THREAD SAFETY ---
# Using a global to check if server is already running
if not 'BEM_LISTENER_EVENT' in globals():
	handler = AuditHandler()
	BEM_LISTENER_EVENT = ExternalEvent.Create(handler)
	BEM_HANDLER = handler


# --- THE SERVER (Background Thread) ---
class BIMRequestHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		try:
			content_length = int(self.headers['Content-Length'])
			post_data = self.rfile.read(content_length)
			payload = json.loads(post_data.decode('utf-8'))

			# 1. Pass data to the handler
			BEM_HANDLER.data_packet = payload

			# 2. Raise the event to run code in Revit
			BEM_LISTENER_EVENT.Raise()

			# 3. Respond to the bash/curl client
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			response = {"status": "accepted", "message": "Revit task queued."}
			self.wfile.write(json.dumps(response).encode('utf-8'))
		except Exception as e:
			self.send_response(500)
			self.end_headers()
			self.wfile.write(str(e).encode('utf-8'))

	def log_message(self, format, *args):
		return  # Suppress standard console logging to keep Revit UI clean


def run_server():
	try:
		server = HTTPServer(('localhost', PORT), BIMRequestHandler)
		server.serve_forever()
	except Exception as e:
		print("Server error: {}".format(e))


# --- MAIN EXECUTION ---
if __name__ == "__main__":
	# Check if a thread is already running on this port
	# In pyRevit, globals persist within the session
	if 'BEM_SERVER_THREAD' in globals():
		forms.alert("The BEM Listener is already active on port {}.".format(PORT))
	else:
		BEM_SERVER_THREAD = threading.Thread(target=run_server)
		BEM_SERVER_THREAD.daemon = True
		BEM_SERVER_THREAD.start()

		print(">>> BEM LISTENER STARTED")
		print(">>> Listening on: http://localhost:{}".format(PORT))
		print(">>> Results will be written to: {}".format(OUTPUT_LOG))

		forms.toast("BEM Listener Active", icon=forms.Icon.INFO)
