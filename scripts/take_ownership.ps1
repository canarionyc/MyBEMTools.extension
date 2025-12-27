# this is done already
# Take ownership of the folder
# takeown /f "C:\repos\pyRevit-Master" /r /d y

# Define the username variable (note the $)
$Username = "DESKTOP-TH1AMMN\Usuario"

# Grant full control using the variable
icacls "C:\repos\pyRevit-Master" /grant "${Username}:F" /t