import requests, base64, datetime
import paramiko, time, csv, os
from flask_mail import Mail, Message

from multiprocessing import Process, Manager
from tsDB import *

#for reserve
import reserveTS as reserveTS
import threading
import multiprocessing

#for send mail
import sendMail as sendMail

# default USERNAME & PASSWORD to connect SSH
USERNAME = 'cfguser'
PASSWORD = 'cfguser'

# define each global variables
relocateTsList = Manager().list()
lockTsList = Manager().list()
message = Manager().list()
tsList = {}
tsList_sanJose = {}
tsList_plano = {}
tsList_bdc = {}
tsList_common = {}
reservedTsList = reserveTS.LinkedList()
relocatedTsList = []

# connectSSH function...try 6 times with waiting 15 seconds
def connectSSH(ip, usn, pwd):
    i = 0
    #while i != 5:
    while i != 1:
        try:
            paramiko.util.log_to_file("paramiko.log")
            # get SSH client from paramiko module
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # establish SSH connection
            print ("\nRemote login to test server: " + usn + " username")
            print ("\nRemote login to test server: " + pwd + " password")
            ssh.connect(ip, port=22, username=usn, password=pwd)
            print ("\nRemote login to test server: " + ip + " successful")
            shell = ssh.invoke_shell(width=120, height=80)
            shell.keep_this = ssh
            
            return shell
        except paramiko.AuthenticationException:
            print ("Authentication failed when connectinig " + ip)
            ssh.close()
            return
        except:
            # if connection fails, try again after 15 seconds
            print ("Could not connect SSH to " + ip + ", waiting 15s for it to start")
            i += 1
            time.sleep(15)
    return

# get TS data from API
def getTSListFromAPI():
    # if tsList is already exist, remove it
    list_sum = len(tsList) + len(tsList_sanJose) + len(tsList_plano) + len(tsList_bdc) + len(tsList_common)
    if list_sum is not 0:
        tsList.clear()
        tsList_bdc.clear()
        tsList_plano.clear()
        tsList_sanJose.clear()
        tsList_common.clear()

    # we already have tasList. Check each tas
    tasList, tasInfoList = TASList.getTASListFromDB()
    for tas in tasList:
        tasAddr = tas
        tasData = TASList.query.filter_by(tasAddress = tasAddr).first()
        tasOwner = tasData.tasName
        tasTeam = tasData.tasTeam

        try:
            # encode necessary data. Use defaulty id/pw(sms:a1b2c3d4)
            encodedAuthData = base64.encodestring('sms:a1b2c3d4').rstrip('\t\r\n\0')

            # add header for the capability for various browsers
            headers = {
                'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                'Authorization' : 'Basic ' + encodedAuthData
            }

            # set the target URL to use API
            URL = 'http://'+ tasAddr +':8080/api/testServers'

            # get the tas data to send API request. Get data by json format
            _tasData = requests.get(URL, headers=headers).json()

            # loop in ts list
            for ts in _tasData['testServers']:
                # send API request again for the ts data. Also get data by json format
                ts['info'] = requests.get(ts['url'], headers=headers).json()

                # store necessary data in the dictionary
                if 'NOT_READY' not in ts['state'] or ts['info']['managementIp'] not in tsList:
                    if 'NOT_READY (NO COMM)' != ts['state']:
                        
                        # If there is TS List in the database
                        if TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first():
                            # bring TS information from database
                            ts_database = TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first()
                            
                            # If TS is a common TS
                            if ts_database.tsCommon == 1:
                                ts_user_name = "Common TS"
                                # update Common TS List                   
                                if ts_database.tsCommon == 1:
                                    tsList_common[ts['info']['managementIp']] = {}
                                    tsList_common[ts['info']['managementIp']]['state'] = ts['state']
                                    tsList_common[ts['info']['managementIp']]['name'] = ts_user_name
                                    tsList_common[ts['info']['managementIp']]['version'] = ts['version']
                                    tsList_common[ts['info']['managementIp']]['info'] = ts['info']
                                    tsList_common[ts['info']['managementIp']]['tas'] = tasAddr
                                    tsList_common[ts['info']['managementIp']]['owner'] = tasOwner

                            # If TS is a private TS
                            else:
                                # If TS doesn't have origin TAS, TS user name is set to located TAS user name
                                if ts_database.originTAS is None:
                                    ts_user_name = "Unknown"

                                # If TS has origin TAS information
                                else:
                                    ts_origin_tas = ts_database.originTAS
                                    tas_database = TASList.query.filter_by(tasAddress = ts_origin_tas).first()

                                    # if origin TAS is not registered to TS Management
                                    if tas_database is None:
                                        ts_user_name = "Unknown"      

                                    # if origin TAS is already registered to TS Management               
                                    else:
                                        # update TS user name as origin TAS's user name
                                        if tas_database.tasName == "Common TAS":
                                            ts_user_name = "Common TS"
                                        else:
                                            ts_user_name = tas_database.tasName
                                        
                        # If there is no TS List in the database
                        else:
                            ts_user_name = "Unknown"

                        # update TS List
                        tsList[ts['info']['managementIp']] = {}
                        tsList[ts['info']['managementIp']]['state'] = ts['state']
                        tsList[ts['info']['managementIp']]['name'] = ts_user_name
                        tsList[ts['info']['managementIp']]['version'] = ts['version']
                        tsList[ts['info']['managementIp']]['info'] = ts['info']
                        tsList[ts['info']['managementIp']]['tas'] = tasAddr
                        tsList[ts['info']['managementIp']]['owner'] = tasOwner
                                
                        # update TS List for team San Jose
                        if tasTeam == 'San Jose':
                            tsList_sanJose[ts['info']['managementIp']] = {}
                            tsList_sanJose[ts['info']['managementIp']]['state'] = ts['state']
                            tsList_sanJose[ts['info']['managementIp']]['name'] = ts_user_name
                            tsList_sanJose[ts['info']['managementIp']]['version'] = ts['version']
                            tsList_sanJose[ts['info']['managementIp']]['info'] = ts['info']
                            tsList_sanJose[ts['info']['managementIp']]['tas'] = tasAddr
                            tsList_sanJose[ts['info']['managementIp']]['owner'] = tasOwner
                        # update TS List for team Plano
                        elif tasTeam == "Plano":
                            tsList_plano[ts['info']['managementIp']] = {}
                            tsList_plano[ts['info']['managementIp']]['state'] = ts['state']
                            tsList_plano[ts['info']['managementIp']]['name'] = ts_user_name
                            tsList_plano[ts['info']['managementIp']]['version'] = ts['version']
                            tsList_plano[ts['info']['managementIp']]['info'] = ts['info']
                            tsList_plano[ts['info']['managementIp']]['tas'] = tasAddr
                            tsList_plano[ts['info']['managementIp']]['owner'] = tasOwner
                        # update TS List for team BDC
                        elif tasTeam == "BDC":
                            tsList_bdc[ts['info']['managementIp']] = {}
                            tsList_bdc[ts['info']['managementIp']]['state'] = ts['state']
                            tsList_bdc[ts['info']['managementIp']]['name'] = ts_user_name
                            tsList_bdc[ts['info']['managementIp']]['version'] = ts['version']
                            tsList_bdc[ts['info']['managementIp']]['info'] = ts['info']
                            tsList_bdc[ts['info']['managementIp']]['tas'] = tasAddr
                            tsList_bdc[ts['info']['managementIp']]['owner'] = tasOwner
                        else:
                            return redirect(url_for('error_404'))

                        # update database if TS already exist
                        if TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first():
                            edit_ts = TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first()
                            edit_ts.tasAddress = tsList[ts['info']['managementIp']]['tas']
                            edit_ts.tsName = ts_user_name
                            edit_ts.tsVersion = ts['version'] 
                            edit_ts.tsState = ts['state']
                            edit_ts.tsManagementIp = ts['info']['managementIp']
                            edit_ts.tsPlatform = ts['info']['platform']
                            edit_ts.tsMemory = ts['info']['memory']
                            edit_ts.tsOS = ts['info']['os']

                            if ts_user_name == "Common TS":
                                edit_ts.tsCommon = 1
                            
                            # update database
                            db.session.commit()
                        
                        # add TS to the database when TS doesn't exist
                        else:
                            new_ts = TSList(tsAddress = ts['info']['managementIp'],
                                            tasAddress = tasAddr, 
                                            tsName = ts_user_name, 
                                            tsVersion = ts['version'], 
                                            tsState = ts['state'], 
                                            tsManagementIp = ts['info']['managementIp'],
                                            tsPlatform = ts['info']['platform'], 
                                            tsMemory = ts['info']['memory'], 
                                            tsOS = ts['info']['os'],
                                            originTAS = None,
                                            tsCommon = 0
                                            )
                            # update database
                            db.session.add(new_ts)
                            db.session.commit()

        except Exception as e:
            return redirect(url_for('error_404'))
    return tsList
    
# check ts is available to relocate or not
def checkTsAvailability(ts):
    if ts in relocateTsList:
        return False
    return True
    
# relocate script for the TS
def modifyTs(ts, targetTas):
    HOST = ts
    TAS = targetTas

    # get SSH connection to HOST TS
    shell = connectSSH(HOST, USERNAME, PASSWORD)
    if shell != None:
        # login as a root	
        shell.send('su\n')
        time.sleep(2)
        rcv = shell.recv(1024)
        print (rcv)

        if b"Password" in rcv:
            shell.send('spirent\n')
            time.sleep(1.5)
            rcv = shell.recv(1024)
            print (rcv)
            shell.send('ifconfig\n')
            time.sleep(1.5)
            rcv = shell.recv(1024)
            print (rcv)

            if HOST in rcv:
                print ("target TS verified")
                shell.send('ipcfg\n')
                time.sleep(1.5)
                rcv = shell.recv(1024)
                print (rcv)

                if b"Continue" in rcv:
                    shell.send('yes\n')
                    time.sleep(13)
                    rcv = shell.recv(1024)
                    print (rcv)

                    while b"TAS IP Address [" not in rcv:
                        shell.send('\n')
                        time.sleep(1.5)
                        rcv = shell.recv(1024)
                        print (rcv)
                    #if TAS in rcv:
                    shell.send(TAS + '\n')
                    time.sleep(1.5)
                    rcv = shell.recv(1024)
                    print (rcv)

                    while b"Reboot now?" not in rcv:
                        shell.send('\n')
                        time.sleep(1.5)
                        rcv = shell.recv(1024)
                        print (rcv)
                    shell.send('\n')
                    time.sleep(1.5)
                    rcv = shell.recv(1024)
                    #else:
                    #	print ("\nThe expected TAS is different...can't modify it")
                else:
                    print ("\nContinue prompt not seen")
            else:
                print ("\nWARNING: Host is different. Wrong target host")
        else:
            print ("\nPassword prompt not seen")
    else:
        print ("\nshell is Empty. Please connect again")
    time.sleep(20)

    # connect SSH and restart TS
    shell = connectSSH(HOST, USERNAME, PASSWORD)
    if shell != None:
            shell.send('su\n')
            time.sleep(2)
            rcv = shell.recv(1024)
            print (rcv)
            shell.send('spirent\n')
            time.sleep(1.5)
            rcv = shell.recv(1024)
            print (rcv)
            shell.send('/home/spcoast/bin/tsd.sh stop\n')
            time.sleep(10)
            rcv = shell.recv(1024)
            print (rcv)
            shell.send('/home/spcoast/bin/tsd.sh start\n')
            time.sleep(1.5)
            rcv = shell.recv(1024)
            print (rcv)
    print ('modifying process is done...remove the ts in relocateTsList')

    # notify that relocating process is done
    for HOST in relocateTsList:
        relocateTsList.remove(HOST)

def logging(ts, targetTas, user):
    # set log entry data
    logEntry = {}
    logEntry['Time'] = str(datetime.datetime.now())
    logEntry['TS'] = ts
    logEntry['Version'] = tsList[ts]['version']
    logEntry['Platform'] = tsList[ts]['info']['platform']
    logEntry['User'] = user
    logEntry['From'] = tsList[ts]['tas'] + '(' + tsList[ts]['owner'] + ')' 
    logEntry['To'] = targetTas.replace(',', '(') + ')'

    # if history.csv is already exist, read it and append
    if os.path.isfile('history.csv'):
        history = {}
        with open('history.csv') as csvfile:
            reader = csv.reader(csvfile)
            field = next(reader)
            for readerIdx, line in enumerate(reader):
                log = {}
                for lineIdx, eachTsLogs in enumerate(line):
                    log[field[lineIdx]] = eachTsLogs
                if log['TS'] not in history:
                    history[log['TS']] = []
                history[log['TS']].append(log)
        if ts not in history:
            history[ts] = []
        history[ts].append(logEntry)

        if len(history[ts]) >= 5:
            # don't need to sort because of the order of file. but leave it to make sure
            # history[ts] = sorted(history[ts], key=lambda k: k['Time'])
            del history[ts][0]

        # after append, re-write to the file
        with open('history.csv', 'wb') as csv_file:
            csvwriter = csv.writer(csv_file, delimiter=',')
            csvwriter.writerow(['Time', 'TS', 'Version', 'Platform', 'User', 'From', 'To'])
            for eachTsLogs in history.values():
                for item in eachTsLogs:
                    csvwriter.writerow([item['Time'],
                                        item['TS'],
                                        item['Version'],
                                        item['Platform'],
                                        item['User'],
                                        item['From'],
                                        item['To']
                                        ])
    else:
        print('initial creating log file')
        with open('history.csv', 'wb') as csv_file:
            csvwriter = csv.writer(csv_file, delimiter=',')
            csvwriter.writerow(['Time', 'TS', 'Version', 'Platform', 'User', 'From', 'To'])
            csvwriter.writerow([logEntry['Time'],
                                logEntry['TS'],
                                logEntry['Version'],
                                logEntry['Platform'],
                                logEntry['User'],
                                logEntry['From'],
                                logEntry['To']
                                ])

# main index dashboard
@app.route('/')
def index():
    """ Session control"""
    if 'email' not in session:
        return render_template('login.html')

    # get error message from session
    if session.get('error') is None:
        error = None
    else:
        error = session.get('error')
        session.pop('error')
    
    # get TAS/TS list from DB
    tasList, tasInfoList = TASList.getTASListFromDB()
    print(tasInfoList)
    getTSListFromAPI()
    print("EUM")

    # define variables for TAS
    email = session['email']
    user = User.query.filter_by(email = email).first()
    userName = user.firstName + " " + user.lastName
    userType = user.userType

    # check if there is modifying TS
    for item in relocateTsList:
        for target in tsList.values():
            if target['info']['managementIp'] == item:
                target['state'] = 'Modifying...'

    # check if there is locked TS
    for item in lockTsList:
        for target in tsList.values():
            if target['info']['managementIp'] == item:
                target['state'] = "LOCK"
    
    # there is no Manager() type string, so using list instead. Once send message, remove it
    tempMessage = ""
    while len(message):
        tempMessage = message[0]
        message.remove(message[0])

    return render_template('tslistview.html', 
                            error=error,
                            tsList=tsList, 
                            tsList_sanJose=tsList_sanJose,
                            tsList_plano=tsList_plano,
                            tsList_bdc=tsList_bdc,
                            tsList_common=tsList_common,
                            tasList=tasInfoList,
                            message=tempMessage,
                            userName=userName,
                            userType=userType)

# route for the about list feature
@app.route('/error_404')
def error_404():
    error = None
    return render_template('error_404.html', error=error)

# route for the lock feature
@app.route('/lock/<ts>')
def locking(ts):
    error = None
    # add target TS to lockTsList
    if ts not in lockTsList:
        lockTsList.append(ts)
    return redirect(url_for('index'))

# route for the unlock feature
@app.route('/unlock/<ts>')
def unlocking(ts):
    error = None
    # remove target TS from lockTSList
    if ts in lockTsList:
        lockTsList.remove(ts)
    return redirect(url_for('index'))

# route for the relocation feature
@app.route('/modify/<ts>/<user>/<tas>')
def tasmodification(ts, user, tas):
    error = None
    tasList, tasInfoList = TASList.getTASListFromDB()                   # get TAS information form the database
    # check TS availability first
    if checkTsAvailability(ts):
        relocateTsList.append(ts)

        # ts modify process
        print (("*")*100)
        target = tas

        # spawn another process for multi-processing
        p = Process(target=modifyTs, args=(ts, tas))
        p.start()
        p.join()
        for tas in tasList:
            if user in tas:
                user = tas.split(',')[1]
                break
        logging(ts, tas, user)
    else:
        # if same TS is already in relocation process, do nothing and send alert message
        print ("WARNING: same TS is already in use!")
        if "same_ts_use" not in message:
            message.append("same_ts_use")

    return redirect(url_for('index'))

#route for edit TAS feature
@app.route('/edit_tas_server', methods=['GET', 'POST'])
def edit_tas_server():
    error = None
    tasList, tasInfoList = TASList.getTASListFromDB()                   # get TAS information form the database
    if request.method == 'POST':
        # get user information from the database
        user_email = session['email']                                   # logged in user email information
        user = User.query.filter_by(email = user_email).first()         # get user information from the database
        user_team = user.team                                           # user's team information (San Jose / Plano / BDC)
        user_type = user.userType                                       # user's type information (admin / guest)
        tasAddr = request.form.get('server-name')                       # TAS addressed typed from the website

        # When you are adding new TAS to the system: you can add common TAS and other user's TAS
        if request.form.get('tas-action-type') == 'add':
            # When user logged in as admin
            userName = user.firstName + " " + user.lastName
            
            # Check whether TAS is already registered
            if TASList.query.filter_by(tasAddress = tasAddr).first() is not None:
                error = "TAS is already registered. Please check."
                session['error'] = error
                return redirect(url_for('index'))                       # return error
            else:
                # update database
                new_tas = TASList(tasAddress=tasAddr, tasUsername=userName, tasTeam=user_team)
                db.session.add(new_tas)
                db.session.commit()

                # flash message success
                flash("TAS edited successfully")
                return redirect(url_for('index'))

        # When you are removing TAS from the system
        elif request.form.get('tas-action-type') == 'remove':
            # Check whether TAS exist
            if TASList.query.filter_by(tasAddress = tasAddr).first() is None:
                error = "TAS doesn't exist. Please use 'Edit TAS' to add your TAS and use this function."
                session['error'] = error
                return redirect(url_for('index'))                       # return error

            else:
                # update database
                delete_tas = TASList.query.filter_by(tasAddress=tasAddr).first()
                db.session.delete(delete_tas)
                db.session.commit()

                # flash message success
                flash("TAS removed successfully")
                return redirect(url_for('index'))
        else:
            error = "Edit TAS Failed. Please try again."
            session['error'] = error
            return redirect(url_for('index'))                           # return error
    else:
        error = "Edit TAS Failed. Please try again."
        session['error'] = error
        return redirect(url_for('index'))                               # return error

    return redirect(url_for('index'))

#route for edit TS feature
@app.route('/edit_ts_server', methods=['GET', 'POST'])
def edit_ts_server():
    error = None
    if request.method == 'POST':
        tasAddr = request.form.get('tas-server-name')
    
        # TS informations from website and database
        temp_ts_1 = request.form.get('ts-server-name-1')                        # website
        temp_ts_2 = request.form.get('ts-server-name-2')                        # website
        selected_ts_1 = TSList.query.filter_by(tsAddress=temp_ts_1).first()     # database
        selected_ts_2 = TSList.query.filter_by(tsAddress=temp_ts_2).first()     # database

        # check whether TAS exist
        if TASList.query.filter_by(tasAddress = tasAddr).first() is None:
            error = "TAS not exist. Please use 'Edit TAS' to add your TAS and use this function."
            session['error'] = error
            return redirect(url_for('index'))                           # return error

        # check wheter TS exist
        if selected_ts_1 is None or selected_ts_2 is None:
            error = "TS not exist. Please mount your TS to TAS manually using LandSlide Application."
            session['error'] = error
            return redirect(url_for('index'))                           # return error

        # update origin TAS information
        selected_ts_1.originTAS = tasAddr
        selected_ts_2.originTAS = tasAddr

        # update database
        db.session.add(selected_ts_1)
        db.session.add(selected_ts_2)
        db.session.commit()

        # flash message success
        flash("Allocated TS successfully")
    else:
        error = "Allocate TS Failed. Please try again."
        session['error'] = error
        return redirect(url_for('index'))                               # return error

    return redirect(url_for('index'))

#route for edit TS feature
@app.route('/edit_common_server', methods=['GET', 'POST'])
def edit_common_server():
    error = None
    if request.method == 'POST':
        # when modifying common TAS
        if request.form.get('common-select-type') == 'tas':
            user_email = session['email']  
            tasAddr = request.form.get('common-servername-tas')         # website
            commonName = "Common TAS"                                   # set new TAS's user name as "Common TAS"
            user = User.query.filter_by(email = user_email).first()     # get user information from the database
            userName = user.firstName + " " + user.lastName
            user_team = user.team                                       # user's team information (San Jose / Plano / BDC)

            # when adding common TAS
            if request.form.get('common-action-type') == 'add':
                selected_tas = TASList.query.filter_by(tasAddress = tasAddr).first()
                if selected_tas is not None:
                    # update TAS user to Common
                    if selected_tas.tasName == "Common TAS":
                        error = "TAS is already a Common TAS. Please check your TAS address."
                        session['error'] = error
                        return redirect(url_for('index'))               # return error
                    else:
                        selected_tas.tasName = commonName
                        # update database
                        db.session.commit()
                        
                        # flash message success
                        flash("Private TAS changed to Common TAS successfully")
                        return redirect(url_for('index'))
                else:
                    # update Common TAS to user
                    selected_tas = TASList(tasAddress=tasAddr, tasUsername=commonName, tasTeam=user_team)
                   
                    # update database
                    db.session.add(selected_tas)
                    db.session.commit()

                    # flash message success
                    flash("TAS successfully added as a Common TAS")
                    return redirect(url_for('index'))
            # when removing common TAS  
            elif request.form.get('common-action-type') == 'remove':
            # Check whether TAS exist
                if TASList.query.filter_by(tasAddress = tasAddr).first() is None:
                    error = "TAS doesn't exist. Please use 'Edit TAS' to add your TAS and use this function."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                else:
                    delete_tas = TASList.query.filter_by(tasAddress=tasAddr).first()
                    if delete_tas.tasName != "Common TAS":
                        error = "TAS is already a Private TAS. Please check your TAS address."
                        session['error'] = error
                        return redirect(url_for('index'))               # return error

                    delete_tas.tasName = userName
                    # update database
                    db.session.commit()

                    # flash message success
                    flash("Common TAS changed to Private TAS successfully")
                    return redirect(url_for('index'))
            else:
                error = "Edit TAS Failed. Please try again."
                session['error'] = error
                return redirect(url_for('index'))                       # return error

        # when modifying common TS       
        else:
            tsAddr_1 = request.form.get('common-servername-ts1')                    # website
            tsAddr_2 = request.form.get('common-servername-ts2')                    # website
            selected_ts_1 = TSList.query.filter_by(tsAddress=tsAddr_1).first()      # database
            selected_ts_2 = TSList.query.filter_by(tsAddress=tsAddr_2).first()      # database

            # when adding common TS
            if request.form.get('common-action-type') == 'add':
                # check wheter TS exist
                if selected_ts_1 is None and selected_ts_2 is None:
                    error = "TS doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_1 is None:
                    error = "TS #1 doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_2 is None:
                    error = "TS #2 doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error

                # check whether TS is already a common TS
                if selected_ts_1.tsCommon == 1:
                    error = "TS #1 is already a Common TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_2.tsCommon == 1:
                    error = "TS #2 is already a Common TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_1.tsCommon == 1 or selected_ts_2.tsCommon == 1:
                    error = "Both TS are already a Common TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error

                # update origin TAS information
                selected_ts_1.tsCommon = 1
                selected_ts_2.tsCommon = 1

                # update database
                db.session.commit()

                # flash message success
                flash("Private TS successfully changed to Common TS")
            # when removing common TS
            else:
                # check wheter TS exist
                if selected_ts_1 is None and selected_ts_2 is None:
                    error = "Both TS doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_1 is None:
                    error = "TS #1 doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_2 is None:
                    error = "TS #2 doesn't exist. Please mount the selected TS to TAS manually using LandSlide Application."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error

                # check whether TS is already a common TS
                if selected_ts_1.tsCommon == 0:
                    error = "TS #1 is already a Private TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_2.tsCommon == 0:
                    error = "TS #2 is already a Private TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error
                elif selected_ts_1.tsCommon == 0 or selected_ts_2.tsCommon == 0:
                    error = "Both TS are already a Private TS. Please check your TS address."
                    session['error'] = error
                    return redirect(url_for('index'))                   # return error

                # update origin TAS information
                selected_ts_1.tsCommon = 0
                selected_ts_2.tsCommon = 0
                selected_ts_1.tsName = "Unknown"
                selected_ts_2.tsName = "Unknown"

                # update database
                db.session.commit()

                # flash message success
                flash("Common TS successfully changed to private TS")
    else:
        error = "Modifying Common TAS/TS Failed. Please try again."
        session['error'] = error
        return redirect(url_for('index'))                               # return error

    return redirect(url_for('index'))

# route for the history list feature
@app.route('/history')
def history():
    error = None
    history = []

    # get data from the file
    with open('history.csv') as csvfile:
        reader = csv.reader(csvfile)
        field = next(reader)
        for readerIdx, line in enumerate(reader):
            log = {}
            for lineIdx, item in enumerate(line):
                log[field[lineIdx]] = item
            history.append(log)

    return render_template('history.html', error=error, history=history)

# route for the about list feature
@app.route('/about')
def about():
    error = None
    return render_template('about.html', error=error)

# route for the main page
@app.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""
    if 'email' in session:
        if request.method == 'POST':
            # send login user information to tslistview.html
            username = getname(request.form['username'])
            return redirect(url_for('index'))
        else:
            # need to send 404 page but skip for now
            return redirect(url_for('error_404'))
    else:
        return render_template('login.html')

# route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Form"""
    error = None
    if request.method == 'POST':
        # if you are logged in, skip this page
        if 'email' in session:
            return redirect(url_for('index'))

        # if you are not logged in, render to login page
        else:
            email = request.form.get('email')
            password = request.form.get('password')

            # login
            if User.authenticate(email, password):
                session['email'] = email
                flash("Logged in successfully")
                return redirect(url_for('home'))

            # if login fails, go back to login page
            else:
                error = "Login Fail"
                return render_template("login.html", error=error)           # return error

    return render_template('login.html')

# route for register
@app.route('/register/', methods=['GET', 'POST'])
def register():
    """Register Form"""
    error = None
    if request.method == 'POST':
        user_email = request.form.get('email')                          # email from the website

        # Check whether email information is unique
        if User.query.filter_by(email = user_email).first() is not None:
            error = "Email already used"
            return render_template('register.html', error=error)        # return error

        new_user = User(email=user_email,                               # add new user information to database
                        password=request.form.get('password'),
                        lastName=request.form.get('lastName'),
                        firstName=request.form.get('firstName'),
                        team=request.form.get('team'),
                        userType=request.form.get('radio'))

        # update database                
        db.session.add(new_user)
        db.session.commit()

        # flash message success
        flash("Registered successfully")

        return render_template('login.html')

    return render_template('register.html')

# route for logout
@app.route("/logout")
def logout():
    """Logout Form"""
    session.pop('email', None)

    # flash message success
    flash("Logged out successfully")

    return redirect(url_for('login'))

@app.route("/reservePage", methods=['GET', 'POST'])
def reservePage():
    """ Session control"""
    if 'email' not in session:
        return render_template('login.html')

    email = session['email']
    user = User.query.filter_by(email = email).first()
    firstName = user.firstName
    lastName = user.lastName
    userName = firstName + " " + lastName
    temp = TASList.query.filter_by(tasName = userName).first()

    if temp is not None:
        myTasAddress = temp.tasAddress
    else:
        myTasAddress = "10.140.92.212"

    todayList = reservedTsList.getTodayReservedList()
    # todayList = []
    # todayList.append((1,3))
    # todayList.append((1,5))
    # todayList.append((2,35))
    
    reservedTSAddrs = []
    for index in range(len(todayList)/12):
        if todayList[12*index + 1] not in reservedTSAddrs:
            reservedTSAddrs.append(todayList[12*index + 1])

    allTsList = []
    for TS in tsList:
        allTsList.append(TS)
    
    return render_template('reservePage.html', 
                            tsList_bdc=tsList_bdc, 
                            tsList_plano=tsList_plano, 
                            tsList_sanJose=tsList_sanJose, 
                            tsList_common=tsList_common,
                            reservedTSAddrs=reservedTSAddrs, 
                            userName=userName, 
                            myTasAddress=myTasAddress,
                            todayList=todayList,
                            allTsList=allTsList
                            )
                            
@app.route('/reservePage/reserve/<startDate>/<day>/<hour>/<minute>/<currentTS>/<relocateTAS>/<reservPerson>', methods=['GET', 'POST'])
def reserve(startDate, day, hour, minute, currentTS, relocateTAS, reservPerson):
    returnTAS = ""
    print(currentTS)
    if currentTS is not None:
        temp = TSList.query.filter_by(tsAddress = currentTS).first()
        if temp:
            if temp.originTAS:
                returnTAS = temp.originTAS
            else:
                returnTAS = "10.140.92.100"
        else:
            returnTAS = "10.140.92.100"
    else:
        return "Null TS selection"

    period, result = reservedTsList.checkPeriod(startDate, day, hour, minute)
    if int(result) != -1:
        isReserved = reservedTsList.reserve(period,currentTS,relocateTAS, returnTAS, result, reservPerson)
        if isReserved is True:
            # flash message success
            flash("Reserved Successfully")
        else:
            flash("Reserve Failed. Interfere other reservation.")
    else:
        flash("Reserve Failed. Time is not valid")
        error = "Reserve Failed"
        session['error'] = error # return error

    return redirect(url_for('reservePage'))

@app.route('/reservePage/reserve2/<startDate>/<day>/<hour>/<minute>/<currentTS>/<currentTS2>/<relocateTAS>/<reservPerson>', methods=['GET', 'POST'])
def reserve2(startDate, day, hour, minute, currentTS, currentTS2, relocateTAS, reservPerson):
    returnTAS = ""
    if currentTS is not None:
        temp = TSList.query.filter_by(tsAddress = currentTS).first()
        if temp:
            if temp.originTAS:
                returnTAS = temp.originTAS
            else:
                returnTAS = "10.140.92.100"
        else:
            returnTAS = "10.140.92.100"
    else:
        return "Null TS selection"

    period, result = reservedTsList.checkPeriod(startDate, day, hour, minute)
    if int(result) != -1:
        isReserved = reservedTsList.reserve(period,currentTS,relocateTAS, returnTAS, result, reservPerson)
        if isReserved is True:
            # flash message success
            flash("Reserved Successfully")
        else:
            flash("Reserve Failed. Interfere other reservation.")
    else:
        flash("Reserve Failed. Time is not valid")
        error = "Reserve Failed"
        session['error'] = error # return error

    returnTAS = ""
    if currentTS2 is not None:
        temp = TSList.query.filter_by(tsAddress = currentTS2).first()
        if temp:
            if temp.originTAS:
                returnTAS = temp.originTAS
            else:
                returnTAS = "10.140.92.100"
        else:
            returnTAS = "10.140.92.100"
    else:
        return "Null TS selection"

    period, result = reservedTsList.checkPeriod(startDate, day, hour, minute)
    if int(result) != -1:
        isReserved = reservedTsList.reserve(period,currentTS2,relocateTAS, returnTAS, result, reservPerson)
        if isReserved is True:
            # flash message success
            flash("Reserved Successfully")
        else:
            flash("Reserve Failed. Interfere other reservation.")
    else:
        flash("Reserve Failed. Time is not valid")
        error = "Reserve Failed"
        session['error'] = error # return error

    return redirect(url_for('reservePage'))

@app.route('/reservePage/cancelReserve/<currentUser>/<index>/<tsAddr>', methods=['GET', 'POST'])
def cancelReserve(currentUser, index,tsAddr):
    result = reservedTsList.cancelReserve(currentUser,int(index),tsAddr)
    if result is not None:
        print(result)
        for reservedItem in relocatedTsList:
            if reservedItem[0] == result[0]:
                relocatedTsList.remove(reservedItem)
                break
        p = Process(target=modifyTs, args=(result[0], result[1]))
        p.start()
        p.join(60) 
    return redirect(url_for('reservePage'))

@app.context_processor
def getBookedList():
    def getbooklist(tsaddr):
        bookedList = reservedTsList.countTsReservationList(tsaddr)
        return bookedList
    return dict(getbooklist=getbooklist)

@app.context_processor
def getMybooklist():
    def getMybooklist(userName):
        mybookedList = reservedTsList.countTsReservationListByName(userName)
        return mybookedList
    return dict(getMybooklist=getMybooklist)

@app.context_processor
def getTeamResevinglist():
    def getTeamResevinglist(team):
        teamReservedList = []
        if team == "SanJose":
            teamTslist = tsList_sanJose
        elif team == "Plano":
            teamTslist = tsList_plano
        elif team == "BDC":
            teamTslist = tsList_bdc
        elif team == "Common":
            teamTslist = tsList_common

        tempState = "on going" #0 = on going , 1 = waiting (reservetime) 2 = available
        for TS in teamTslist.values():
            tempState = reservedTsList.getIsOnGoing(TS['info']['managementIp'])
            teamReservedList.append(tempState)
        return teamReservedList
    return dict(getTeamResevinglist=getTeamResevinglist)

def relocateReservedTS():
    global relocatedTsList
    global session
    global reservedTsList
    if (datetime.datetime.now().minute % 5) == 0:
        #check if the relcating correctly
        for relocatedTs in relocatedTsList:
            temp = TSList.query.filter_by(tsAddress = relocatedTs[0]).first()
            if temp.tasAddress != relocatedTs[1]:
                #if ts is not belongs to reserved tas, send mail
                wrongTAS = TASList.query.filter_by(tasAddress = temp.tasAddress).first()
                if wrongTAS is not None:
                    temp_ = wrongTAS.tasName.split(' ')
                    temp_firstName = ""
                    if temp_firstName is not None:
                        temp_firstName = temp_[0]
                    temp_lastName = ""
                    if temp_lastName is not None:
                        temp_lastName = temp_[1]                    
                    ReceiverName = User.query.filter_by(firstName = temp_firstName).filter_by(lastName = temp_lastName).first()
                    if ReceiverName is not None:
                        print("try to send mail to ", ReceiverName, " and ", ReceiverName.email)
                        Context = "The TS : " + relocatedTs[0] + " is reserved for now.\nPlease relocate TS to TAS : " + relocatedTs[1] +"\n\nThank you"
                        sendMail.send_mail(temp_lastName +"."+ temp_firstName +"@spirent.com", Context)
                        print("send mail successfully")
                    else:
                        print("Receiver is None")
                else:
                    print("wrongTAS is None")

        relocateTSList = reservedTsList.display_list()
        print(relocateTSList)
        fromTAS = ""
        for element in relocateTSList:
            print(element[2])
            if element[2] == True:
                relocatedTsList.append((element[0], element[1])) #ts addr, tas addr
                print ("add true case")
                print (relocatedTsList)
                #locking(element[0])
            else:
                print ("before delete false case")
                print (relocatedTsList)
                #unlocking(element[0])
                for reservedItem in relocatedTsList:
                    if reservedItem[0] == element[0]:
                        relocatedTsList.remove(reservedItem)
                        break
                print ("after delete false case")
                print (relocatedTsList)

            fromTAS = tsList[element[0]]['tas']
            p = Process(target=modifyTs, args=(element[0], element[1]))
            p.start()
            p.join(60)           
            #tasmodification(element[0], fromTAS, element[1])
    
    # if (datetime.datetime.now().minute % 10) == 0:
    #     #check if the relcating correctly
    #     for relocatedTs in relocatedTsList:
    #         temp = TSList.query.filter_by(tsAddress = relocatedTs[0]).first()
    #         if temp.tasAddress != relocatedTs[1]:
    #             #if ts is not belongs to reserved tas, relocate again
    #             tasmodification(relocatedTs[0], temp.tasAddress, relocatedTs[1])
    print("minute : " , datetime.datetime.now().minute)
    print ("relocated are")
    print (relocatedTsList)
    reservedTsList.showList()
    threading.Timer(60, relocateReservedTS).start()

def send_email(senders, receiver, content):
    try:
        mail = Mail(app)
        msg = Message('Title', sender = senders, recipients = receiver)
        msg.body = content
        mail.send(msg)
    except Exception:
        pass
    finally:
        pass

relocateReservedTS()