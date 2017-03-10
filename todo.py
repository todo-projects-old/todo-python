#!/usr/bin/python3

import os
import io
import re
import sys
import time
import datetime
import configparser
from subprocess import Popen, PIPE

class Todo:
    config = None
    
    projectKeys = ['p', 'prj', 'project']
    priorityKeys = ['t', 'top', 'priority']
    idKeys = ['i', 'id']
    nameKeys = ['n', 'name']
    userKeys = ['u', 'user', 'username']
    scopeKeys = ['s', 'scope']
    messageKeys = ['m', 'msg', 'message']
    
    @staticmethod
    def initConfig():
        Todo.config = configparser.ConfigParser()
        Todo.config['Issues'] = {
            'dir_names': ['issues'],
            'default_priority': 'B',
            'default_scope': '',
            'extension': '.md',
            'file_name_separator': '.',
            'id_seq_file': 'todo.conf',
            'local_seq_file': True
        }
        Todo.config['User'] = {
            'name': 'Unknown'
        }
        configPathes = [os.path.expanduser('~') + '/.todo/todo.conf', 'todo.conf']
        for path in configPathes:
            if os.path.isfile(path):
                Todo.config.read(path)
    
    @staticmethod
    def getConfig():
        if Todo.config == None:
            Todo.initConfig()
        return Todo.config
    
    @staticmethod
    def getIssuesDirNames():
        return Todo.getConfig()['Issues']['dir_names']
    
    @staticmethod
    def getIssuesDirList():
        issuesDirList = []
        for root, subdirs, files in os.walk('.'):
            for subdir in subdirs:
                if subdir in Todo.getIssuesDirNames():
                    issuesDirList.append(os.path.join(root, subdir))
        #print(issuesDirList)
        return issuesDirList
    
    @staticmethod
    def getActualIssuesDirName(root):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path) and f in Todo.getIssuesDirNames():
                return f
        return None
    
    @staticmethod
    def getIssueData(path):
        if path.startswith('./'):
            path = path[2:]
        for d in Todo.getIssuesDirNames():
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
    
    @staticmethod
    def parseArg(arg):
        param = None
        index = arg.find(':')
        if index >= 0:
            param = {
                'key': arg[0:index],
                'value': arg[index + 1:]
            }
        return param 

class MemIO:
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.memin = io.StringIO()
        self.memout = io.StringIO()

    def inToMem(self):
        sys.stdin = self.memin
    
    def inToStdin(self):
        sys.stdin = self.stdin
    
    def outToMem(self):
        sys.stdout = self.memout
    
    def outToStdout(self):
        sys.stdout = self.stdout
 
    def switch(self):
        self.memout.seek(0)
        self.memin = self.memout
        self.memout = io.StringIO()
        self.inToMem()
        self.outToMem()
    
    def reset(self):
        self.inToStdin()
        self.outToStdout()
    
class Add:
    def __init__(self):
        self.name = 'add'
    
    @staticmethod
    def getDefaultIssueParams():
        return {
            'user': Todo.getConfig()['User']['name'],
            'root': '.',
            'issues_dir': None,
            'top': Todo.getConfig()['Issues']['default_priority'],
            'seq_file_name': Todo.getConfig()['Issues']['id_seq_file'],
            'ext': Todo.getConfig()['Issues']['extension'],
            'sep': Todo.getConfig()['Issues']['file_name_separator'],
            'id': None,
            'scope': Todo.getConfig()['Issues']['default_scope'],
            'name': ''
        }
    
    @staticmethod
    def seqNextId(root, seqFileName):
        nextId = None
        if len(seqFileName) > 0:
            if Todo.getConfig()['Issues']['local_seq_file']:
                path = os.path.join(root, seqFileName)
                if not os.path.isfile(path):
                    path = os.path.join('.', seqFileName)
            else:
                path = seqFileName
            if os.path.isfile(path):
                seqFile = open(path, 'r+')
                nextId = int(seqFile.read().strip())
                seqFile.seek(0)
                seqFile.write(str(nextId + 1))
                seqFile.truncate()
                seqFile.close()
        return nextId
    
    @staticmethod
    def createNewIssue(params):
        path = os.path.join(params['root'], params['issues_dir'], params['scope'], '')
        if not os.path.exists(path):
            os.makedirs(path)
        
        allParts = params['name']
        if params['id'] and params['name']:
            allParts = params['sep'] + allParts
        allParts = params['id'] + allParts
        if params['top'] and allParts:
            allParts = params['sep'] + allParts
        allParts = params['top'] + allParts
       
        issue = path + allParts + params['ext']
        if os.path.exists(issue):
            print("Issue is exist: " + issue)
            sys.exit(1)
        open(issue, 'a').close()
        print(issue)
    
    def run(self, args):
        params = Add.getDefaultIssueParams()
        for arg in args:
            param = Todo.parseArg(arg)
            if param != None:
                if param['key'] in Todo.projectKeys:
                    memio = MemIO()
                    memio.outToMem()
                    List.printProjects(params['root'])
                    memio.switch()
                    f = Filter()
                    f.run([param['value']])
                    memio.switch()
                    s = Sort()
                    s.run([])
                    memio.switch()
                    memio.outToStdout()
                    for line in sys.stdin:
                        params['root'] = line.strip()
                        break
                elif param['key'] in Todo.priorityKeys:
                    params['top'] = param['value']
                elif param['key'] in Todo.idKeys:
                    params['id'] = param['value']
                elif param['key'] in Todo.nameKeys:
                    params['name'] = param['value']
                elif param['key'] in Todo.userKeys:
                    params['user'] = param['value']
                elif param['key'] in Todo.scopeKeys:
                    params['scope'] = param['value']
            else:
                if params['name'] != '':
                    params['name'] += ' '
                params['name'] += arg
        params['issues_dir'] = Todo.getActualIssuesDirName(params['root'])
        if params['issues_dir'] == None:
            print("Issues dir not found")
            sys.exit(1)
            
        if params['id'] == None:
            nextId = Add.seqNextId(params['root'], params['seq_file_name'])
            if nextId != None:
                params['id'] = str(nextId)
            else:
                params['id'] = params['user'] + '_' + str(int(time.time()))
        Add.createNewIssue(params)

class List:    
    @staticmethod
    def printIssues(root, inIssues):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                List.printIssues(path, inIssues or (f in Todo.getIssuesDirNames()))
            elif inIssues and os.path.isfile(path):
                print(path)
    
    @staticmethod
    def printProjects(root):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                if f in Todo.getIssuesDirNames():
                    print(root)
                else:
                    List.printProjects(path)
    
    @staticmethod
    def getProjectPathes(root, pathes=[]):
        for f in os.listdir(root):
            path = os.path.join(root, f)
            if os.path.isdir(path):
                if f in Todo.getIssuesDirNames():
                    pathes.append(root)
                else:
                    List.getProjectPathes(path, pathes)
        return pathes

    def __init__(self):
        self.name = 'list'
        
    def run(self, args):
        projectsMode = False
        for arg in args:
            if arg in Todo.projectKeys:
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
            print(data['project'] + "\t" + data['scope'] + "\t" + data['name'])
    
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
                print(line)

class Sort:
    def __init__(self):
        self.name = 'sort'
        
    def run(self, args):
        lines = sys.stdin.readlines()           
        lines.sort()
        for line in lines:
            line = line.strip()
            print(line)

class Comment:
    def __init__(self):
        self.name = 'comment'

    def run(self, args):
        msg = ''
        user = Todo.getConfig()['User']['name']
        for arg in args:
            param = Todo.parseArg(arg)
            if param != None:
                if param['key'] in Todo.messageKeys:
                    msg = param['value']
                elif param['key'] in Todo.userKeys:
                    user = param['value']
        if msg:
            msg += '\n'
        for line in sys.stdin:
            line = line.strip()
            header = '# ' + user + ' ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fh = open(line, 'rb')
            statinfo = os.stat(line)
            if statinfo.st_size > 8:
                fh.seek(-8, 2)
            rawLines = fh.readlines()
            content = '\n' + header + '\n\n' + msg
            if len(rawLines) > 0 and rawLines[-1][-1] != 10:
                content = '\n' + content
            fh.close()
            fh = open(line, 'a')
            fh.write(content)
            fh.close()
            print(line)


COMMANDS = [
    {'names': ['a', 'add'], 'handler': Add()},
    {'names': ['l', 'list'], 'handler': List()},
    {'names': ['v', 'view'], 'handler': View()},
    {'names': ['d', 'do', 'util'], 'handler': Do()},
    {'names': ['f', 'filter'], 'handler': Filter()},
    {'names': ['s', 'sort'], 'handler': Sort()},
    {'names': ['c', 'comment'], 'handler': Comment()}
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
    memio = MemIO()
    memio.outToMem()
    for index, command in enumerate(commands):
        if index == len(commands) - 1:
            memio.outToStdout()
        handler = getHandler(command['name'])
        if handler is not None:
            handler.run(command['args'])
        else:
            memio.outToStdout()
            print("Command not found: " + command['name'])
            sys.exit(1)
        memio.switch()
main()
