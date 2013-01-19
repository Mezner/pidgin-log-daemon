import os

# Directory in which your Pidgin logs are. Usually this is a .purple directory
# under your user's home location.
LOG_DIRECTORY=os.environ['PIDGIN_LOG_DIRECTORY']

# Developer token provided by Evernote. This gives full access to your Evernote
# account and should be secured as if it were your password.
#
# A token can be generated at https://www.evernote.com/api/DeveloperToken.action
DEVELOPER_TOKEN=os.environ['EVERNOTE_DEVELOPER_TOKEN']

# The notebook that notes will be added to.
LOG_NOTEBOOK_NAME="Pidgin Log"

# Polling interval in seconds
POLL_INTERVAL=10
