#!/usr/bin/python 

import os
import io
import sys
import datetime
from subprocess import Popen, PIPE

class Todo:
    issuesDirs = ['issues']
    
    @staticmethod
    def getIssuesDirList():
        issuesDirList = []
        for root, subdirs, files in os.walk('.'):
            for subdir in subdirs:
                if subdir in Todo.issuesDirs:
                    issuesDirList.append(os.path.join(root, subdir))
        #print issuesDirList
        return issuesDirList    
    
    @staticmethod
    def getIssueData(path):
        if path.startswith('./'):
            path = path[2:]
        for d in Todo.issuesDirs:
            separator = '/' + d + '/'
            index = path.find(separator)
            if index >= 0:
                lastSlash = path.rfind('/')
                return {
                    'project': path[0:index],
                    'scope': path[index + len(separator):lastSlash],
                    'name': path[lastSlash + 1:]
                }
        
        
class List:
    @staticmethod
    def printIssues(root, inIssues):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                List.printIssues(path, inIssues or (f in Todo.issuesDirs))
            elif inIssues and os.path.isfile(path):
                print path
    
    def __init__(self):
        self.name = 'list'
        
    def run(self, args):
        List.printIssues('.', False)


class View:
    @staticmethod
    def printInLine():
        for line in sys.stdin:
            line = line.strip()
            data = Todo.getIssueData(line)
            print data['project'] + "\t" + data['scope'] + "\t" + data['name']
    
    def __init__(self):
        self.name = 'view'
        
    def run(self, args):
        View.printInLine()


class Do:
    def __init__(self):
        self.name = 'do'
        
    def run(self, args):
        for line in sys.stdin:
            line = line.strip()
            args.append(line)
        execute(args)


COMMANDS = [
    {'names': ['l', 'list'], 'handler': List()},
    {'names': ['v', 'view'], 'handler': View()},
    {'names': ['d', 'do', 'util'], 'handler': Do()}
]

def execute(args):
    proc = Popen(args)
    out, err = proc.communicate()
    
def getHandler(name):
    for command in COMMANDS:
        for commandName in command['names']:
            if name == commandName:
               return command['handler'] 
    return None
 
def main():
    commands = []
    firstArg = sys.argv[1]
    multiCommandMode = firstArg.startswith('-')
    if not multiCommandMode:
        commands.append({'name': firstArg, 'args': sys.argv[2:]})
    else:
        name = None
        args = []
        for arg in sys.argv[1:]:
            if arg.startswith('-'):
                if name is not None:
                    commands.append({'name': name, 'args': args})
                    args = []
                if arg.startswith('--'):
                    name = arg[2:]
                else:
                    name = None
                    for short in arg[1:]:
                        if name is not None:
                            commands.append({'name': name, 'args': []})
                        name = short
            else:
                args.append(arg)
        if name is not None:
            commands.append({'name': name, 'args': args})
    stdin = sys.stdin
    stdout = sys.stdout
    memin = io.BytesIO()
    memout = io.BytesIO()
    for index, command in enumerate(commands):
        if index != 0:
            sys.stdin = memin
        else:
            sys.stdin = stdin
        if index != len(commands) - 1:
            sys.stdout = memout
        else:
            sys.stdout = stdout
        handler = getHandler(command['name'])
        if handler is not None:
            handler.run(command['args'])
        else:
            sys.stdout = stdout
            print "Command not found: " + command['name']
            sys.exit(1)
        memout.seek(0)
        memin = memout
        memout = io.BytesIO()
main()
