python-log-daemon
=================

Python-log-daemon is a linux daemon written in Python that can translate your Pidgin HTML logs to notes in Evernote.

Currently Pidgin can write logs to disk and, in Windows, Evernote can import these logs into specific notebooks in your account.

This has a few problems:
* It flat out does not work in Linux. While you can run Evernote via Wine without much an issue, the file import feature does not seem to work.
* When importing a log you only get a choice of what Notebook to put it in. You can't really change the title of the note (as it is based on the filename) or add tags.
* Directory recursion only goes one level deep. This effectively means that for every account you import logs for, you must create a new import rule in Evernote.
