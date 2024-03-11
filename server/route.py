from server.Server import server, jsonifyPlus, request, render_template, abort, login_user, logout_user, current_user, User, login_required, userM, redirect
from flask import render_template_string
from server.palRcon import PalM

@server.route('/')
def home():
    '''home page'''
    return redirect('/apidocs')

@server.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register
    ---
    tags:
      - register
    
    produces: application/json,
    
    parameters:
    - name: email     
      in: query
      type: str
      required: false
      description: the user's email, will be key
    - name: username     
      in: query
      type: str
      required: false
      description: the user's name
    - name: password     
      in: query
      type: str
      required: false
      description: the user's password
    
    responses:
      401:
        description: "The email has be used."
      200:
        description: success register.
        example: "{'message':'admin register success.'}"
    """
    id = request.values.get('email')
    if userM.User.get(id): return jsonifyPlus({'message':f'user: {id} has been exist.'}),401
    username = request.values.get('username')
    password = request.values.get('password')
    userM.User(id,username,password)
    return jsonifyPlus({'message':f'{id} register success.'})

@server.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changePassword():
    """
    Change Password
    ---
    tags:
      - change password
    
    produces: application/json,
    
    parameters:
    - name: oldpassword     
      in: query
      type: str
      required: false
      description: old password
    - name: newpassword     
      in: query
      type: str
      required: false
      description: new password
    
    responses:
      403:
        description: "Old password error."
      200:
        description: success register.
        example: "{'message':'admin change password success.'}"
    """
    oldpassword = request.values.get('oldpassword')
    ID = current_user.get_id()
    server.logger.debug(f'user:{ID}; oldPassw:{oldpassword}')
    userDaya:userM.User = userM.User.get(ID)
    if userDaya.PASSWORD != oldpassword: return jsonifyPlus({'message':f'user: {userDaya.ID} old password error.'}),403
    newpassword = request.values.get('newpassword')
    userDaya.set(PASSWORD=newpassword)
    return jsonifyPlus({'message':f'{id} change password success.'})

@server.route('/changename', methods=['GET', 'POST'])
@login_required
def changeName():
    """
    Change Name
    ---
    tags:
      - change name
    
    produces: application/json,
    
    parameters:
    - name: name     
      in: query
      type: str
      required: false
      description: disply name
    
    responses:
      200:
        description: success register.
        example: "{'message':'admin change password success.'}"
    """
    userDaya:userM.User = userM.User.get(current_user.id)
    name = request.values.get('name')
    userDaya.set(NAME=name)
    return jsonifyPlus({'message':f'{id} change name success.'})

@server.route('/login', methods=['GET', 'POST'])
def login():
    """
    LOGIN
    ---
    tags:
      - login
    
    produces: application/json,
    
    parameters:
    - name: email     
      in: query
      type: str
      required: false
      description: the user's name
    - name: password     
      in: query
      type: str
      required: false
      description: the user's password
    
    responses:
      401:
        description: "Not find the user."
      403:
        description: "Password error."
      200:
        description: success login.
        example: "{'message':'admin login success.'}"
    """
    id = request.values.get('email')
    if not id in userM.User.USERS: return jsonifyPlus({'message':f'not find user: {id}.'}),401
    if not (request.values.get('password') == userM.User.USERS[id].PASSWORD):
        server.logger.error(f'{id} login fail with password error: {request.values.get("password")}')
        return jsonifyPlus({'message':f'{id} login fail with password error.'}),403
    user = User()
    user.id = id
    login_user(user)
    return jsonifyPlus({'message':f'{id} login success.'})
    

@server.route('/logout')
def logout():
    """
    LOGOUT
    ---
    tags:
      - logout
    
    produces: application/json,
    
    responses:
      200:
        description: success logout current user.
        example: "{'message':'admin logout success.'}"
    """
    id = current_user.get_id()
    logout_user()
    return jsonifyPlus({'message':f'{id} logout success.'})

@server.route('/testLogger')
def testLogger():
    """
    Test Logger
    ---
    tags:
      - test logger
    
    produces: application/json,
    
    responses:
      200:
        description: success logout current user.
        example: "{'message':'admin logout success.'}"
    """
    server.logger.info("Info message")
    server.logger.warning("Warning msg")
    server.logger.error("Error msg!!!")
    server.logger.debug("Debug msg!!!")

    return jsonifyPlus({'message':'test success.'})

@server.route('/rcon/send', methods=['GET','POST'])
@login_required
def rconSend():
    """
    Send a commend to Pal Server RCON
    ---
    tags:
      - RCON send
    
    produces: application/json,
    
    parameters:
    - name: command     
      in: query
      type: str
      required: false
      description: the command to send
    - name: args     
      in: query
      type: arry[str]
      required: false
      description: the args to send, use multiple times to add args.
    
    responses:
      502:
        description: "Can not start because the Pal Server disable Rcon func."
      200:
        description: success Send a message to Pal Server RCON.
        example: "{'response': 'response from Pal.'}"
    """
    command = request.values.get('command')
    server.logger.debug(f'command = {command}')
    args= request.values.getlist('args',type=str)
    server.logger.debug(f'args = {args}')
    if command:
        response = PalM.RCONSend(command, *args)
    return jsonifyPlus({'response': response})

@server.route('/pal')
@login_required
def palIndex():
    """
    Pal Server Info Page
    ---
    tags:
      - pal page
    
    produces: application/json,
    
    responses:
      200:
        description: success get pal page.
    """
    return render_template('pal.html',name='Pal',propertys=PalM.getSettings())

@server.route('/pal/get')
@login_required
def palGet():
    """
    Pal Server Info Get
    ---
    tags:
      - pal get
    
    produces: application/json,
    
    responses:
      200:
        description: success get pal set.
    """
    result = PalM.getSettings()
    return jsonifyPlus(result)

@server.route('/pal/set', methods=['GET','POST'])
@login_required
def palSet():
    """
    設定 Pal Server optionsettings 
    ---
    tags:
      - Server set

    produces: application/json,

    parameters:
    - name: DayTimeSpeedRate
      in: query
      type: str
      required: false
      description: Day time speed
    - name: NightTimeSpeedRate   
      in: query
      type: str
      required: false
      description: Night time speed
    - name: ExpRate
      in: query
      type: str
      required: false
      description: EXP rate
    - name: PalCaptureRate
      in: query
      type: str
      required: false
      description: Pal capture rate
    - name: PalSpawnNumRate
      in: query
      type: str
      required: false
      description: "Pal Appearance Rate *Note: Affects game performance"
    - name: PalDamageRateAttack
      in: query
      type: str
      required: false
      description: Damage from Pals Multiplier
    - name: PalDamageRateDefense
      in: query
      type: str
      required: false
      description: Damage to Pals Multiplier
    - name: PlayerDamageRateAttack
      in: query
      type: str
      required: false
      description: Damage from Player Multiplier
    - name: PlayerDamageRateDefense
      in: query
      type: str
      required: false
      description: Damage to Player Multiplier
    - name: PlayerStomachDecreaceRate
      in: query
      type: str
      required: false
      description: Player Hunger Depletion Rate
    - name: PlayerStaminaDecreaceRate
      in: query
      type: str
      required: false
      description: Player Stamina Reduction Rate
    - name: PlayerAutoHPRegeneRate
      in: query
      type: str
      required: false
      description: Player Auto Health Regeneration Rate
    - name: PlayerAutoHpRegeneRateInSleep
      in: query
      type: str
      required: false
      description: Player Sleep Health Regeneration Rate
    - name: PalStomachDecreaceRate
      in: query
      type: str
      required: false
      description: Pal Hunger Depletion Rate
    - name: PalStaminaDecreaceRate
      in: query
      type: str
      required: false
      description: Pal Stamina Reduction Rate
    - name: PalAutoHPRegeneRate
      in: query
      type: str
      required: false
      description: Pal Auto Health Regeneration Rate
    - name: PalAutoHpRegeneRateInSleep
      in: query
      type: str
      required: false
      description: "Pal Sleep Health Regeneration Rate (Health Regeneration Rate in Palbox)"
    - name: BuildObjectDamageRate
      in: query
      type: str
      required: false
      description: Damage to Structure Multiplier
    - name: BuildObjectDeteriorationDamageRate
      in: query
      type: str
      required: false
      description: Structure Deterioration Rate
    - name: CollectionDropRate
      in: query
      type: str
      required: false
      description: Gatherable Items Multiplier
    - name: CollectionObjectHpRate
      in: query
      type: str
      required: false
      description: Gatherable Objects Health Multiplier
    - name: CollectionObjectRespawnSpeedRate
      in: query
      type: str
      required: false
      description: Gatherable Objects Respawn Interval
    - name: EnemyDropItemRate
      in: query
      type: str
      required: false
      description: Dropped Items Multiplier
    - name: DeathPenalty
      in: query
      type: str
      required: false
      description: Death Penalty
    - name: bEnableInvaderEnemy
      in: query
      type: str
      required: false
      description: Enable Invader
    - name: GuildPlayerMaxNum
      in: query
      type: str
      required: false
      description: Max Player Number of Guilds
    - name: PalEggDefaultHatchingTime
      in: query
      type: str
      required: false
      description: "Time (h) to incubate Massive Egg. Note: Other eggs also require time to incubate."
    - name: ServerPlayerMaxNum
      in: query
      type: str
      required: false
      description: Maximum number of players that can join the server
    - name: ServerName
      in: query
      type: str
      required: false
      description: Server name
    - name: ServerDescription
      in: query
      type: str
      required: false
      description: Server description
    - name: AdminPassword
      in: query
      type: str
      required: false
      description: Password used to obtain administrative privileges on the server.
    - name: ServerPassword
      in: query
      type: str
      required: false
      description: Password required for server login
    - name: PublicPort
      in: query
      type: str
      required: false
      description: "Explicitly specify the external public port in the community server configuration.（This setting does not change the server's listen port.）"
    - name: PublicIP
      in: query
      type: str
      required: false
      description: Explicitly specify an external public IP in the community server settings
    - name: RCONEnabled
      in: query
      type: str
      required: false
      description: Enable RCON
    - name: RCONPort
      in: query
      type: str
      required: false
      description: Port Number for RCON
    - name: bShowPlayerList
      in: query
      type: str
      required: false
      description: Enable player list when the press ESC key
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success save settings to Pal Server, return server setting.
        examples: "info: 'Welcome to someone's pal"
    """
    configs = {}
    for key in PalM.getServer()._settings.keys():
        temp = request.values.get(key, type=str)
        if temp: configs[key]=temp
    result = PalM.setSettings(**configs)

    return jsonifyPlus(result)

@server.route('/cnfig/get')
@login_required
def cnfigGet():
    """
    Server Cnfig Get
    ---
    tags:
      - cnfig get
    
    produces: application/json,
    
    responses:
      200:
        description: success get cnfig settings.
    """
    result = PalM.getConfig()
    return jsonifyPlus(result)

@server.route('/cnfig/set', methods=['GET','POST'])
@login_required
def cnfigSet():
    """
    設定 Pal Server steamroot, palservicename
    ---
    tags:
      - Cnfig set

    produces: application/json,
    parameters:
    - name: steamroot     
      in: query
      type: str
      required: false
      description: Steam root path
    - name: palservicename   
      in: query
      type: str
      required: false
      description: Name of Pal World server service
    - name: settingsrelatepath   
      in: query
      type: str
      required: false
      description: settings file relate path from steam root
    responses:
      401:
        description: Unauthorized error
      200:
        description: success save Config to System, return Config.
    """
    keys = ['steamroot', 'palservicename','settingsrelatepath']
    configs = {}
    for key in keys:
        temp = request.values.get(key, type=str)
        if temp: configs[key]=temp

    result = PalM.setConfig(**configs)

    return jsonifyPlus(result)

@server.route('/pal/start', methods=['GET','POST'])
@login_required
def palStart():
    """
    Pal Service start.
    ---
    tags:
      - Pal start

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success start pal service.
    """
    result = PalM.start()

    return jsonifyPlus({'status': result})

@server.route('/pal/stop', methods=['GET','POST'])
@login_required
def palStop():
    """
    Pal Service stop.
    ---
    tags:
      - Pal stop

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success stop pal service.
    """
    result = PalM.stop()

    return jsonifyPlus({'status': result})

@server.route('/pal/restart', methods=['GET','POST'])
@login_required
def palRestart():
    """
    Pal Service restart.
    ---
    tags:
      - Pal restart

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success restart pal service.
    """
    result = PalM.restart()

    return jsonifyPlus({'status': result})

@server.route('/pal/status', methods=['GET','POST'])
def palStatus():
    """
    Get Pal Service status.
    ---
    tags:
      - Pal status

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success Get pal service status.
    """
    result = PalM.status()

    return jsonifyPlus({'status': result})


@server.route('/pal/update', methods=['GET','POST'])
@login_required
def palUpdate():
    """
    Pal Service update.
    ---
    tags:
      - Pal update

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success update pal server.
    """
    result = PalM.update()

    return jsonifyPlus({'status': result})

@server.route('/pal/serviceinfo', methods=['GET','POST'])
@login_required
def palServiceInfo():
    """
    Get Pal Service Info.
    ---
    tags:
      - Pal serviceinfo

    produces: application/json,
    
    responses:
      401:
        description: Unauthorized error
      200:
        description: success get Pal service info.
    """
    result = PalM.getPalServiceInfo()

    return jsonifyPlus({'status': result})
    