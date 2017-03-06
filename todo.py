#!/usr/bin/python 

import os
import io
import re
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
            if path.startswith(separator[1:]):
                index = 0
            else:
                index = path.find(separator)
            if index >= 0:
                lastSlash = path.rfind('/')
                return {
                    'project': path[0:index],
                    'scope': path[index + len(separator):lastSlash],
                    'name': path[lastSlash + 1:]
                }

class Add:
    def __init__(self):
        self.name = 'add'
        
    def run(self, args):
        for arg in args:
            line = line.strip()
            args.append(line)
        execute(args)


class List:
    projectCommands = ['p', 'prj', 'project', 'projects']
    @staticmethod
    def printIssues(root, inIssues):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                List.printIssues(path, inIssues or (f in Todo.issuesDirs))
            elif inIssues and os.path.isfile(path):
                print path
    
    @staticmethod
    def printProjects(root):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                if f in Todo.issuesDirs:
                    print root
                else:
                    List.printProjects(path)
                
    def __init__(self):
        self.name = 'list'
        
    def run(self, args):
        projectsMode = False
        for arg in args:
            if arg in List.projectCommands:
                projectsMode = True
        if projectsMode:
            List.printProjects('.')
        else:
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

class Filter:
    def __init__(self):
        self.name = 'filter'
        
    def run(self, args):
        regexp = None
        if len(args) > 0:
            regexp = re.compile(args[0])
        for line in sys.stdin:
            line = line.strip()
            if (regexp == None) or (regexp.search(line) != None):
                print line

class Sort:
    def __init__(self):
        self.name = 'sort'
        
    def run(self, args):
        lines = sys.stdin.readlines()           
        lines.sort()
        for line in lines:
            line = line.strip()
            print line


COMMANDS = [
    {'names': ['l', 'list'], 'handler': List()},
    {'names': ['v', 'view'], 'handler': View()},
    {'names': ['d', 'do', 'util'], 'handler': Do()},
    {'names': ['f', 'filter'], 'handler': Filter()},
    {'names': ['s', 'sort'], 'handler': Sort()}
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
