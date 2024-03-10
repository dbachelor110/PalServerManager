from rcon.source.client import Client, Packet
from rcon.source.proto import Type, LittleEndianSignedInt32, EmptyResponse, IO, TERMINATOR
from urllib.parse import quote, unquote
from server.Server import server, abort, DETAIL
from time import sleep
import queue
import configparser
import subprocess
import asyncio
from string import Template

LOGGER = server.logger

__all__ = ["PalM", "RCON", "MClient", "MPacket"]

class MPacket(Packet):
    @classmethod
    def read(cls, file: IO) -> Packet:
        """Read a packet from a file-like object."""
        LOGGER.log(DETAIL,"Reading packet.")
        LOGGER.log(DETAIL,"  => name: %i", file.name)
        size = LittleEndianSignedInt32.read(file)
        LOGGER.log(DETAIL,"  => size: %i", size)
        if not size:
            raise EmptyResponse()
        id_ = LittleEndianSignedInt32.read(file)
        LOGGER.log(DETAIL,"  => id: %i", id_)
        type_ = Type.read(file, prefix="  ")
        LOGGER.log(DETAIL,"  => type: %i", type_)
        fullFile:bytes = file.read(size)
        LOGGER.log(DETAIL,"  => fullFile: %s", fullFile)
        LOGGER.log(DETAIL,"  => file Len: %s", len(fullFile))
        payload = fullFile[:-2]
        LOGGER.log(DETAIL,"  => payload: %s", payload)
        terminator = fullFile[-2:]
        LOGGER.log(DETAIL,"  => terminator: %s", fullFile[-2:])
        if terminator != TERMINATOR:
            LOGGER.warning("Unexpected terminator: %s", terminator)

        return cls(id_, type_, payload, terminator)

class MClient(Client):
    def run(self, command: str, *args: str, encoding: str = "utf-8", enforce_id: bool = False) -> str:
        LOGGER.debug('run...')
        newArgs = [quote(command)]
        for arg in args:
            newArgs.append(quote(arg))
        
        LOGGER.debug(f'newArgs = {newArgs}')

        return unquote(super().run(newArgs[0], *newArgs[1:], encoding=encoding, enforce_id=enforce_id))
    
    def sendCommand(
        self, command: str, *args: str, encoding: str = "utf-8"):
        """Send a command."""
        newArgs = []
        for arg in args:
            newArgs.append(quote(arg))
        request = MPacket.make_command(command, *newArgs, encoding=encoding)
        self.send(request)
    
    def read(self) -> MPacket:
        """Read a packet from the server."""
        with self._socket.makefile("rb", buffering=0, encoding="utf-8",errors='ignore') as file:
            response = MPacket.read(file)
            if len(response.payload) < self.frag_threshold:
                return response
            self.send(MPacket.make_command(self.frag_detect_cmd))
            while (successor := MPacket.read(file)).id == response.id:
                response += successor
        return response
    def readUnquote(self):
        response = self.read()
        return unquote(response.payload.decode())

class RCON:
    def __init__(self,host,port,password, timeout=1.0) -> None:
        self.HOST = host
        self.PORT = int(port)
        self.PASSWORD = password
        self.MESSAGESQ = queue.Queue()
        self.TIMEOUT = timeout
        self.connect = True
        self.test()
    
    def config(self,host,port,password, timeout=1.0):
        """update settings"""
        self.HOST = host
        self.PORT = int(port)
        self.PASSWORD = password
        self.TIMEOUT = timeout
        self.test()
    
    def run(self, command: str, *args: str):
        self.test()
        if not self.connect: return 'RCON disconnect.'
        with MClient(self.HOST,self.PORT,passwd=self.PASSWORD,timeout=self.TIMEOUT)as client:
            message = client.run(command, *args)
        return message
    
    def test(self):
        LOGGER.debug('RCON connect test...')
        info = ''
        try:
            with MClient(self.HOST,self.PORT,passwd=self.PASSWORD,timeout=10.0)as client:
                info = client.run('info')
            self.connect = True
            LOGGER.log(DETAIL,f"info = {info}")
            return info

        except:
            self.connect = False
            return False
class BasePal:
    def __init__(self) -> None:
        self.settingsRelatePath = 'steamapps/common/PalServer/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini'
        self.configIniPath = 'config.ini'
        self._settings = {}
        self.hotSettings = ['ServerName','CoopPlayerMaxNum','ServerPassword','PublicPort','PublicIP','RCONEnabled','RCONPort','AdminPassword']
        self._environmentVars = {}
        self._ConfigParser=configparser.ConfigParser()
        self.RCON = RCON('localhost',8211,'Password')
        self.SERVERPROCESS = None
        self.SERVERTEMPLATE = self._makeServiceTemplates()
        self.initialConfig()
        pass

    def getSettingsIniPath(self):
        return f'{self._environmentVars["steamroot"]}/{self.settingsRelatePath}'


    class Setting:
        def __init__(self,key:str,value,hot:bool=False) -> None:
            self.key=key
            self.value=value
            self.hot=hot

    def initialConfig(self):
        self._getConfig()
        self._getSettings()
    
    def _upDateRcon(self):
        self.RCON.config(self._settings['PublicIP'],self._settings['RCONPort'],self._settings['AdminPassword'])

    def _getSettings(self):
        """from .ini file get optionsettings and return as dict"""
        self._ConfigParser.read(self.getSettingsIniPath(), encoding='utf-8')
        preConfig = self._ConfigParser["/Script/Pal.PalGameWorldSettings"]["optionsettings"]
        config = self._iniToDict(preConfig)
        self._settings = config
        self._ConfigParser.clear()
        self._upDateRcon()
        return config
    
    def _saveSettings(self, **kargs):
        """save dict to .ini file -> ["/Script/Pal.PalGameWorldSettings"]["optionsettings"]"""
        optionsettings = self._dictToIni(kargs)
        self._ConfigParser.read(self.getSettingsIniPath(), encoding='utf-8')
        self._ConfigParser["/Script/Pal.PalGameWorldSettings"]["optionsettings"] = optionsettings
        with open(self.getSettingsIniPath(), 'w', encoding='utf-8') as configfile:
            self._ConfigParser.write(configfile)
        self._ConfigParser.clear()
    
    def _getConfig(self):
        self._ConfigParser.read(self.configIniPath, encoding='utf-8')
        temp = self._ConfigParser.sections()
        if not 'environment' in temp:
            self._ConfigParser.add_section('environment')
            self._ConfigParser.set('environment','steamroot','~/steam')
            self._ConfigParser.set('environment','palservicename','palServer')
            with open(self.configIniPath, 'w', encoding='utf-8') as configfile:
                self._ConfigParser.write(configfile)
        temp = {}
        for key, value in self._ConfigParser['environment'].items():
            temp[key] = value
        LOGGER.info(f'GET ENV Vars: {temp}')
        self._environmentVars = temp
        self._ConfigParser.clear()
        return temp
    
    def _saveConfig(self, **kargs):
        """save dict to .ini file -> ["environment"]"""
        for key in kargs.keys():
            if key in self._environmentVars:
                self._environmentVars[key]=kargs[key]
                LOGGER.info(f'SAVE ENV {key}: {kargs[key]}')
        
        self._ConfigParser.read(self.configIniPath, encoding='utf-8')
        self._ConfigParser["environment"].update(self._environmentVars)
        with open(self.configIniPath, 'w', encoding='utf-8') as configfile:
            self._ConfigParser.write(configfile)
        self._ConfigParser.clear()

    def _dictToIni(self,inputData:dict) -> str:
        """translate dict to .ini type str"""
        outStr = '('
        for key, value in inputData.items():
            newValue = None
            boolAndNone = ['True','False','None']
            try:
                float(value)
                newValue = value
            except:
                if value in boolAndNone:
                    newValue = value
                else:
                    newValue = f'\"{value}\"'
            outStr += f'{key}={newValue},'
        outStr = outStr[:-1] + ')'
        return outStr
    
    def _iniToDict(self,inputData:str) -> dict:
        """translate .ini str to dict"""
        outDict = {}
        temps = inputData.strip('()').split(',')
        for temp in temps:
            kvpare = temp.split('=')
            if len(kvpare)<2: continue
            outDict[kvpare[0]] = kvpare[1].strip('\"')
        return outDict
    
    async def start_server(self):
        LOGGER.log(DETAIL,"Starting server...")
        # 这里替换为您启动服务器的命令
        steamRoot = self._environmentVars["steamroot"]
        command = f'{steamRoot}/steamapps/common/PalServer/PalServer.sh -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS'
        if self._settings["RCONEnabled"] == 'True':
            RCONPort = self._settings["RCONEnabled"]
            command += f'-RCONEnabled=True -RCONPort={RCONPort}'
        if self._settings['PublicPort']:
            PublicPort = self._settings['PublicPort']
            command += f'-PublicPort={PublicPort}'
        process = await asyncio.create_subprocess_exec(f"{command}", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await process.wait()
        LOGGER.log(DETAIL,"Server started.")

    async def stop_server(process):
        LOGGER.log(DETAIL,"Stopping server...")
        process.terminate()  # 替换为合适的终止命令
        await process.wait()
        LOGGER.log(DETAIL,"Server stopped.")
    
    def _makeServiceTemplates(self):
        ServiceTemplates=Template("""[Unit]
Description=Palworld Server

[Service]
WorkingDirectory=/home/steam/steam/steamapps/common/PalServer

ExecStart=/bin/bash -c "$command "

LimitNOFILE=100000
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s INT $MAINPID

Restart=always
RestartSec=10

User=steam
Group=steam
# Set the syslog identifier
SyslogIdentifier=palServer

# Redirect standard output and standard error to log files
StandardOutput=append:/home/steam/Steam/palServer/logs/palServer_output.log
StandardError=append:/home/steam/Steam/palServer/logs/palServer_error.log
[Install]
WantedBy=multi-user.target""")
        return ServiceTemplates
    
    def _updatePalService(self):
        # make command
        command = f'{self._environmentVars["steamroot"]}/steamapps/common/PalServer/PalServer.sh -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS'
        if self._settings['RCONEnabled'] == 'True':
            command += f'-RCONEnabled=True -RCONPort={self._settings["RCONEnabled"]}'
        if self._settings['PublicPort']:
            command += f'-PublicPort={self._settings["PublicPort"]}'
        Service = self.SERVERTEMPLATE.substitute(command=command)
        filePath = f'/etc/systemd/system/{self._environmentVars["palservicename"]}.service'
        with open(filePath,'w',encoding='utf-8')as file:
            file.write(Service)
        result = subprocess.run(f'sudo chmod 644 {filePath}', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        result = subprocess.run(f'sudo systemctl daemon-reload', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        return result
    
    def catPalService(self):
        filePath = f'/etc/systemd/system/{self._environmentVars["palservicename"]}.service'
        result = subprocess.run(f'cat {filePath}', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        return result

    def status(self):
        result = subprocess.run(f'sudo systemctl status {self._environmentVars["palservicename"]}', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        LOGGER.info('status successful')
        return result

    def start(self):
        result = subprocess.run(f'sudo systemctl start {self._environmentVars["palservicename"]}', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        LOGGER.info('start successful')
        return self.status()

    def stop(self):
        result = subprocess.run(f'sudo systemctl stop {self._environmentVars["palservicename"]}', shell=True, capture_output=True, text=True)
        LOGGER.log(DETAIL,result)
        LOGGER.info('stop successful')
        return self.status()
    
    def restart(self):
        self.stop()
        sleep(5)
        self.start()
        return self.status()

    def update(self):
        self.stop()
        result = subprocess.run(f'{self._environmentVars["steamroot"]}/steamcmd.sh +login anonymous +app_update 2394010 validate +quit',
                                shell=True, capture_output=True, text=True)
        LOGGER.info('updating...')
        self.start()

    def getSettings(self):
        temp = self._settings
        return temp
    
    def getEnvVars(self):
        temp = self._environmentVars
        return temp

class checkServer(object):
    def __init__(self, f):
        self.f = f
    
    def __call__(self, *args, **kwargs):
        PalM.getServer()
        return self.f(*args, **kwargs)
    
class PalM:
    _SERVER:BasePal = None
    BPal = BasePal

    def getServer():
        if not PalM._SERVER:
            PalM._SERVER = PalM.BPal()
        return PalM._SERVER
    
    @checkServer
    def getSettings():
        """get PalM._SERVER._settings"""
        return PalM._SERVER.getSettings()
    
    @checkServer
    def setSettings(**kargs):
        """set kargs to PalM._SERVER._settings
        
        the setting do not working untill server restart."""
        for key in PalM._SERVER._settings.keys():
            if key in kargs:
                PalM._SERVER._settings[key] = kargs[key]
        PalM._SERVER._saveSettings(**PalM._SERVER._settings)
        PalM._SERVER._updatePalService()
        return PalM._SERVER._settings
    
    @checkServer
    def getConfig():
        """get PalM._SERVER._environmentVars"""
        return PalM._SERVER.getEnvVars()
    
    @checkServer
    def setConfig(**kargs):
        """set kargs to PalM._SERVER._environmentVars"""
        for key in PalM._SERVER._environmentVars.keys():
            if key in kargs:
                PalM._SERVER._environmentVars[key] = kargs[key]
        PalM._SERVER._saveConfig(**PalM._SERVER._environmentVars)
        return PalM._SERVER.getEnvVars()

    @checkServer
    def start():
        return PalM._SERVER.start()
    
    @checkServer
    def stop():
        return PalM._SERVER.stop()
    
    @checkServer
    def status():
        return PalM._SERVER.status()
    
    @checkServer
    def update():
        return PalM._SERVER.update()
    
    @checkServer
    def restart():
        return PalM._SERVER.restart()
    
    @checkServer
    def getPalServiceInfo():
        return PalM._SERVER.catPalService()
    
    @checkServer
    def RCONSend(command: str, *args: str):
        return PalM._SERVER.RCON.run(command,*args)

    # def cleanConfig():
    #     """quit the setting in PalM._SERVER._config, and reload setting in .ini file."""
    #     PalM._SERVER.initialConfig()




                            
