cd "C:\repos\pyRevit-Master"

# Fetch all updates from GitHub
git fetch --all

# Switch to the actual develop branch
git checkout develop

# Ensure it's up to date
git reset --hard origin/develop

pyrevit update