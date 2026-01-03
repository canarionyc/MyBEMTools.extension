#! python3
from pyrevit import HOST_APP, framework
from pyrevit import UI, DB


# This must match the signature of your original handler exactly
def docchanged_eventhandler(sender, args):
    pass


# We attempt to wrap it again and subtract it
# Sometimes this works if the delegate signature matches perfectly
cleanup_handler = framework.EventHandler[DB.Events.DocumentChangedEventArgs](
    docchanged_eventhandler
)

try:
    # We attempt to unregister it multiple times in case you clicked 'Run'
    # multiple times while testing.
    for _ in range(10):
        HOST_APP.app.DocumentChanged -= cleanup_handler

    print("Cleanup attempt finished. Try modifying an element to see if the popups stopped.")
except Exception as e:
    print("Could not unregister: {}".format(e))