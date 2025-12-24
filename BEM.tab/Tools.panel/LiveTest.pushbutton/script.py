import sys, io
# Create a memory buffer to catch all prints
revit_buffer = io.StringIO()
sys.stdout = revit_buffer

# YOUR UNTOUCHED LEGACY CODE BELOW:
print("!!! SCRIPT IS LOADING !!!")
print("System path: {}".format(sys.path))
print("Hello! Everything is working now.")

from pyrevit import output
# Once the script is done, send the whole buffer to the UI at once
output.get_output().print_md(revit_buffer.getvalue().replace('\x00', ''))