import sys
import os
import clr
import json
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# 1. Standard Revit API Imports
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import IExternalEventHandler, ExternalEvent


# 2. THE WORKER: This runs inside the Revit Main Thread
class AuditHandler(IExternalEventHandler):
	def __init__(self):
		self.task_data = None
		self.output_path = r"C:\Users\Public\audit_out.json"

	def Execute(self, app):
		try:
			doc = app.ActiveUIDocument.Document
			# --- YOUR BIM LOGIC HERE ---
			walls = FilteredElementCollector(doc).OfClass(Wall).GetElementCount()

			result = {
				"status": "success",
				"model": doc.Title,
				"wall_count": walls,
				"received_command": self.task_data
			}
			# ---------------------------
			with open(self.output_path, "w") as f:
				f.write(json.dumps(result))

		except Exception as e:
			with open(self.output_path, "w") as f:
				f.write(json.dumps({"error": str(e)}))

	def GetName(self):
		return "BEM Audit Listener"


# 3. GLOBAL INSTANCES
handler = AuditHandler()
external_event = ExternalEvent.Create(handler)


# 4. THE LISTENER: This runs in the Background
class RequestHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		content_length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(content_length)

		# Pass data to the handler and trigger the event
		handler.task_data = json.loads(post_data)
		external_event.Raise()

		self.send_response(200)
		self.end_headers()
		self.wfile.write("Task Sent to Revit")


def run_server():
	server = HTTPServer(('localhost', 8080), RequestHandler)
	print("Revit Listener active on port 8080...")
	server.serve_forever()


# Start server in a background thread so Revit doesn't freeze
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

print("LISTENER INITIALIZED: You can now send commands from bash.")