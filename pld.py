#!/usr/bin/python
import sys
sys.path.append('lib')

import time
from daemon import runner
import hashlib
import binascii
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
from bs4 import BeautifulSoup, NavigableString
import bleach
import os
from logsettings import *

class PythonLogDaemon():
    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/pld.pid'
        self.pidfile_timeout = 5
        self.log_directory = LOG_DIRECTORY
        self.developer_token = DEVELOPER_TOKEN
        self.poll_interval = 10
    def run(self):
        while True:
            time.sleep(self.poll_interval)
            importer = PythonLogImporter(self.developer_token, self.log_directory)
            importer.import_logs()

class PythonLogImporter():
    def __init__(self, developer_token, log_directory):
        self.developer_token = developer_token
        self.log_directory = log_directory

    def import_logs(self):
        print "Importing logs..."
        evernoteHost = "www.evernote.com"
        userStoreUri = "https://" + evernoteHost + "/edam/user"
        PERMITTED_TAGS = ['a', 'abbr','acronym','address','area','b','bdo','big','blockquote','br','caption','center','cite','code','col','colgroup','dd','del','dfn','div','dl','dt','em','font','h1','h2','h3','h4','h5','h6','hr','i','img','ins','kbd','li','map','ol','p','pre','q','s','samp','small','span','strike','strong','sub','sup','table','tbody','td','tfoot','th','thead','title','tr','tt','u','ul','var','xmp', 'br/']
        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        userStore = UserStore.Client(userStoreProtocol)
        versionOK = userStore.checkVersion("Pidgin Log Importer",
            UserStoreConstants.EDAM_VERSION_MAJOR,
            UserStoreConstants.EDAM_VERSION_MINOR)
        print "Evernote API up-to-date:", str(versionOK)
        if not versionOK:
            exit(1)
        noteStoreUrl = userStore.getNoteStoreUrl(self.developer_token)
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        noteStore = NoteStore.Client(noteStoreProtocol)

        print "Determining if Pidgin log notebook exists..."
        notebooks = noteStore.listNotebooks(self.developer_token)
        logNotebookExists = False
        for notebook in notebooks:
            if notebook.name == "Pidgin Log":
                logNotebookExists = True
                logNotebook = notebook
                break
        if logNotebookExists:
            print "Pidgin log notebook exists."
        else:
            print "Pidgin log notebook does not exist. Creating..."
            logNotebook = Types.Notebook(name="Pidgin Log")
            logNotebook = noteStore.createNotebook(self.developer_token, logNotebook)
        for root, subFolders, files in os.walk(self.log_directory):
            for filename in files:
                extension = os.path.splitext(filename)[-1].lower()
                if extension == '.html':
                    filePath = os.path.join(root, filename)
                    print filePath
                    soup = BeautifulSoup(open(filePath))
                    noteTitle = soup.title.get_text()
                    cleanLog = bleach.clean(soup.body.prettify(), tags=PERMITTED_TAGS, attributes={'*': ['color', 'size']}, strip=True)
                    cleanLog = "<div>" + cleanLog + "</div>"
                    soup = BeautifulSoup(cleanLog)
                    noteContent = '<?xml version="1.0" encoding="UTF-8"?>'
                    noteContent += '<!DOCTYPE en-note SYSTEM ' \
                        '"http://xml.evernote.com/pub/enml2.dtd">'
                    noteContent += '<en-note>'
                    noteContent += str(soup.body.div.extract())
                    noteContent += '</en-note>'
                    noteFilter = NoteStore.NoteFilter(notebookGuid=logNotebook.guid, words='intitle:"' + noteTitle + '"')
                    existingNotes = noteStore.findNotes(self.developer_token, noteFilter, 0, 1)
                    if existingNotes.totalNotes > 0:
                        note = existingNotes.notes[0]
                        print "Found existing note:", note.guid
                    else:
                        note = Types.Note()
                    note.title = noteTitle
                    note.content = noteContent
                    note.notebookGuid = logNotebook.guid
                    if existingNotes.totalNotes > 0:
                        note = noteStore.updateNote(self.developer_token, note)
                        print "Updated note: ", note.guid
                    else:
                        note = noteStore.createNote(self.developer_token, note)
                        print "Created note: ", note.guid
logDaemon = PythonLogDaemon()
daemonRunner = runner.DaemonRunner(logDaemon)
daemonRunner.do_action()
