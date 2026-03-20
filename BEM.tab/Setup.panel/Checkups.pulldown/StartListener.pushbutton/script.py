#! python 3
import sys
import threading
from io import StringIO
from System.Net import HttpListener
from System.Text import Encoding

# --- 1. CONFIGURATION ---
PORT = 48884
URL = "http://localhost:{}/BEM/exec/".format(PORT)

# --- 2. THE EXECUTION LOGIC ---
def handle_request(context):
    try:
        # Read the incoming script from the POST body
        request = context.Request
        reader = sys.modules['System.IO'].StreamReader(request.InputStream, Encoding.UTF8)
        code = reader.ReadToEnd()
        
        # Setup output capture
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        try:
            # Execute the code
            exec(code, globals())
            output = redirected_output.getvalue()
            response_text = output if output else "Success: Script executed."
            status = 200
        except Exception as e:
            response_text = "Python Error: " + str(e)
            status = 500
        finally:
            sys.stdout = old_stdout

        # Send response back to PowerShell
        buffer = Encoding.UTF8.GetBytes(response_text)
        response = context.Response
        response.StatusCode = status
        response.ContentType = "text/plain"
        response.ContentLength64 = buffer.Length
        response.OutputStream.Write(buffer, 0, buffer.Length)
        response.OutputStream.Close()
        
    except Exception as e:
        print("Listener Error: " + str(e))

# --- 3. THE BACKGROUND SERVER ---
def start_server():
    listener = HttpListener()
    listener.Prefixes.Add(URL)
    try:
        listener.Start()
        print("BEM Iron-Bridge Active at: " + URL)
        while listener.IsListening:
            context = listener.GetContext()
            # Handle each request in its own thread so Revit doesn't freeze
            t = threading.Thread(target=handle_request, args=(context,))
            t.start()
    except Exception as e:
        print("Could not start server: " + str(e))
    finally:
        listener.Close()

# Start the listener in a background thread
bg_thread = threading.Thread(target=start_server)
bg_thread.daemon = True
bg_thread.start()