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
        importer = PythonLogImporter(self.developer_token, self.log_directory)
        importer.startup()
        while True:
            time.sleep(self.poll_interval)
            importer.import_logs()

class PythonLogImporter():
    def __init__(self, developer_token, log_directory):
        self.developer_token = developer_token
        self.log_directory = log_directory
        self.PERMITTED_TAGS = ['a', 'abbr','acronym','address','area','b','bdo','big','blockquote','br','caption','center','cite','code','col','colgroup','dd','del','dfn','div','dl','dt','em','font','h1','h2','h3','h4','h5','h6','hr','i','img','ins','kbd','li','map','ol','p','pre','q','s','samp','small','span','strike','strong','sub','sup','table','tbody','td','tfoot','th','thead','title','tr','tt','u','ul','var','xmp', 'br/']
        self.logNotebookName = LOG_NOTEBOOK_NAME

    def startup(self):
        evernoteHost = "www.evernote.com"
        userStoreUri = "https://" + evernoteHost + "/edam/user"
        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        self.userStore = UserStore.Client(userStoreProtocol)
        versionOK = self.userStore.checkVersion("Pidgin Log Importer",
            UserStoreConstants.EDAM_VERSION_MAJOR,
            UserStoreConstants.EDAM_VERSION_MINOR)
        print "Evernote API up-to-date:", str(versionOK)
        if not versionOK:
            exit(1)
        noteStoreUrl = self.userStore.getNoteStoreUrl(self.developer_token)
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
        self.noteStore = NoteStore.Client(noteStoreProtocol)

        print "Determining if Pidgin log notebook exists..."
        notebooks = self.noteStore.listNotebooks(self.developer_token)
        logNotebookExists = False
        for notebook in notebooks:
            if notebook.name == self.logNotebookName:
                logNotebookExists = True
                self.logNotebook = notebook
                break
        if logNotebookExists:
            print "Pidgin log notebook exists."
        else:
            print "Pidgin log notebook does not exist. Creating..."
            self.logNotebook = Types.Notebook(name=self.logNotebookName)
            self.logNotebook = self.noteStore.createNotebook(self.developer_token, logNotebook)

    def import_logs(self):
        print "Importing logs..."
        for root, subFolders, files in os.walk(self.log_directory):
            for filename in files:
                extension = os.path.splitext(filename)[-1].lower()
                if extension == '.html':
                    filePath = os.path.join(root, filename)
                    self._import_log_file(filePath)
        print "Importing complete."

    def _import_log_file(self, filePath):
        print filePath
        soup = BeautifulSoup(open(filePath))
        noteTitle = soup.title.get_text()
        noteContent = self.__get_content_from_soup(soup)
        noteFilter = NoteStore.NoteFilter(notebookGuid=self.logNotebook.guid, words='intitle:"' + noteTitle + '"')
        existingNotes = self.noteStore.findNotes(self.developer_token, noteFilter, 0, 1)
        if existingNotes.totalNotes > 0:
            note = existingNotes.notes[0]
            note = self.noteStore.getNote(self.developer_token, note.guid, True, False, False, False)
            if note.content == noteContent:
                print "Note is up to date. Ignoring."
                return
        else:
            note = Types.Note()
        note.title = noteTitle
        note.content = noteContent
        note.notebookGuid = self.logNotebook.guid
        if existingNotes.totalNotes > 0:
            note = self.noteStore.updateNote(self.developer_token, note)
            print "Updated note: ", note.guid
        else:
            note = self.noteStore.createNote(self.developer_token, note)
            print "Created note: ", note.guid

    def __get_content_from_soup(self, soup):
        cleanLog = bleach.clean(soup.body.prettify(), tags=self.PERMITTED_TAGS, attributes={'*': ['color', 'size']}, strip=True)
        cleanLog = "<div>" + cleanLog + "</div>"
        soup = BeautifulSoup(cleanLog)
        noteContent = '<?xml version="1.0" encoding="UTF-8"?>'
        noteContent += '<!DOCTYPE en-note SYSTEM ' \
            '"http://xml.evernote.com/pub/enml2.dtd">'
        noteContent += '<en-note>'
        noteContent += str(soup.body.div.extract())
        noteContent += '</en-note>'
        return noteContent

logDaemon = PythonLogDaemon()
daemonRunner = runner.DaemonRunner(logDaemon)
daemonRunner.do_action()
