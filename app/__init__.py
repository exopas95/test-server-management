import requests, base64, datetime
import paramiko, time, csv, os
#from flask_mail import Mail, Message

from multiprocessing import Process, Manager
from tsDB import *

#for reserve
import reserveTS as reserveTS
import threading
import multiprocessing

# default USERNAME & PASSWORD to connect SSH
USERNAME = 'cfguser'
PASSWORD = 'cfguser'

# define each global variables
relocateTsList = Manager().list()
lockTsList = Manager().list()
message = Manager().list()
tsList = {}
tasList, tasInfoList = TASList.getTASListFromDB()
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
        except:
            # if connection fails, try again after 15 seconds
            print ("Could not connect SSH to " + ip + ", waiting 15s for it to start")
            i += 1
            time.sleep(15)

# get TS data from API
def getTSListFromAPI():
    # if tsList is already exist, remove it
    if len(tsList) is not 0:
        tsList.clear()

    # we already have tasList. Check each tas
    #originTASaddr = ""
    for tas in tasList:
        tasAddr = tas
        temp = TASList.query.filter_by(tasAddress = tasAddr).first()
        tasOwner = temp.tasName
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
            tasData = requests.get(URL, headers=headers).json()

            # loop in ts list
            for ts in tasData['testServers']:
                # send API request again for the ts data. Also get data by json format
                ts['info'] = requests.get(ts['url'], headers=headers).json()

                # store necessary data in the dictionary
                if 'NOT_READY' not in ts['state'] or ts['info']['managementIp'] not in tsList:
                    if 'NOT_READY (NO COMM)' != ts['state']:
                        tsList[ts['info']['managementIp']] = {}
                        tsList[ts['info']['managementIp']]['state'] = ts['state']
                        tsList[ts['info']['managementIp']]['name'] = ts['name']
                        tsList[ts['info']['managementIp']]['version'] = ts['version']
                        tsList[ts['info']['managementIp']]['info'] = ts['info']
                        tsList[ts['info']['managementIp']]['tas'] = tasAddr
                        tsList[ts['info']['managementIp']]['owner'] = tasOwner

                        if TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first():
                            edit_ts = TSList.query.filter_by(tsAddress = ts['info']['managementIp']).first()
                            # originTASaddr = edit_ts.originTAS
                            # if originTASaddr == "":
                            #     originTASaddr = tasAddr

                            edit_ts.tasAddress = tsList[ts['info']['managementIp']]['tas']
                            edit_ts.tsName = ts['name'] 
                            edit_ts.tsVersion = ts['version'] 
                            edit_ts.tsState = ts['state']
                            edit_ts.tsManagementIp = ts['info']['managementIp']
                            edit_ts.tsPlatform = ts['info']['platform']
                            edit_ts.tsMemory = ts['info']['memory']
                            edit_ts.tsOS = ts['info']['os']#,
                            #edit_ts.originTAS = originTASaddr

                            #originTASaddr = ""
                            # db.session.delete(edit_ts)
                            # db.session.commit()

                        else:
                            new_ts = TSList(tsAddress = ts['info']['managementIp'],
                                            tasAddress = tasAddr, 
                                            tsName = ts['name'], 
                                            tsVersion = ts['version'], 
                                            tsState = ts['state'], 
                                            tsManagementIp = ts['info']['managementIp'],
                                            tsPlatform = ts['info']['platform'], 
                                            tsMemory = ts['info']['memory'], 
                                            tsOS = ts['info']['os'],
                                            originTAS = tasAddr
                                            )
                            db.session.add(new_ts)
                            db.session.commit()

        except Exception as e:
            print ("error")
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
    time.sleep(45)

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

    email = session['email']
    user = User.query.filter_by(email = email).first()
    firstName = user.firstName
    lastName = user.lastName
    userName = firstName + " " + lastName
    print(userName)
    temp = TASList.query.filter_by(tasName = userName).first()
    print(temp)

    if temp is not None:
        myTasAddress = temp.tasAddress
    else:
        myTasAddress = "10.140.92.100"

    getTSListFromAPI()
    tempMessage = ""

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
    while len(message):
        tempMessage = message[0]
        message.remove(message[0])

    return render_template('tslistview.html', tsList=tsList, tasList=tasInfoList, message=tempMessage, userName=userName, myTasAddress=myTasAddress)

# route for the lock feature
@app.route('/lock/<ts>')
def locking(ts):
    # add target TS to lockTsList
    if ts not in lockTsList:
        lockTsList.append(ts)
    return redirect(url_for('index'))

# route for the unlock feature
@app.route('/unlock/<ts>')
def unlocking(ts):
    # remove target TS from lockTSList
    if ts in lockTsList:
        lockTsList.remove(ts)
    return redirect(url_for('index'))

# route for the relocation feature
@app.route('/modify/<ts>/<user>/<tas>')
def tasmodification(ts, user, tas):
    # check TS availability first
    if checkTsAvailability(ts):
        relocateTsList.append(ts)

        # ts modify process
        print (("*")*100)
        target = tas

        # spawn another process for multi-processing
        p = Process(target=modifyTs, args=(ts, tas))
        p.start()

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

@app.route('/edit_server', methods=['GET', 'POST'])
def edit_server():
    if request.method == 'POST':
        email = session['email']
        user = User.query.filter_by(email = email).first()
        firstName = user.firstName
        lastName = user.lastName
        userName = firstName + " " + lastName

        if request.form.get('action-type') == 'add':
            new_tas = TASList(tasAddress=request.form.get('server-name'), tasUsername=userName)
            db.session.add(new_tas)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            delete_tas = TASList(tasAddress=request.form.get('server-name'), tasUsername=userName)
            db.session.delete(delete_tas)
            db.session.commit()
            return redirect(url_for('index'))
    else:
        print("error2")
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

@app.route('/', methods=['GET', 'POST'])
def home():
    """ Session control"""
    if 'email' in session:
        if request.method == 'POST':
            username = getname(request.form['username'])
            return render_template('tslistview.html', data=getfollowedby(username))
        return render_template('tslistview.html')
    else:
        return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Form"""
    if 'email' in session:
        return redirect(url_for('index'))
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        if User.authenticate(email, password):
            session['email'] = email
        return redirect(url_for('home'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    """Register Form"""
    if request.method == 'POST':
        new_user = User(email=request.form.get('email'), 
                        password=request.form.get('password'),
                        lastName=request.form.get('lastName'),
                        firstName=request.form.get('firstName'),
                        team=request.form.get('team',
                        userType=request.fomr.get('radio')))
        db.session.add(new_user)
        db.session.commit()
        return render_template('login.html')
    return render_template('register.html')

@app.route("/logout")
def logout():
    """Logout Form"""
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route("/reservePage")
def reservePage():
    return render_template('reservePage.html')

@app.route('/reserve/<mon1>/<dat1>/<hou1>/<min1>/<ampm1>/<mon2>/<dat2>/<hou2>/<min2>/<ampm2>/<currentTS>/<relocateTAS>/<reservPerson>', methods=['GET', 'POST'])
def reserve(mon1, dat1, hou1, min1, ampm1, mon2, dat2, hou2, min2, ampm2, currentTS, relocateTAS, reservPerson):
    print(mon1, dat1, hou1, min1, ampm1, mon2, dat2, hou2, min2, ampm2)
    returnTAS = ""
    if currentTS is not None:
        temp = TSList.query.filter_by(tsAddress = currentTS).first()
        returnTAS = temp.originTAS
    else:
        return "Null TS selection"

    starttime, result = reservedTsList.checkPeriod(int(mon1), int(dat1), int(hou1), int(min1), int(ampm1), int(mon2), int(dat2), int(hou2), int(min2), int(ampm2))
    if int(result) != -1:
        reservedTsList.reserve(starttime,currentTS,relocateTAS, returnTAS, result, reservPerson)

    return redirect(url_for('index'))

@app.route('/cancelReserve/<tsAddrToCancel>/<index>', methods=['GET', 'POST'])
def cancelReserve(tsAddrToCancel, index):
    print(tsAddrToCancel , index)
    reservedTsList.cancelReserve(tsAddrToCancel,int(index))
    return redirect(url_for('index'))

@app.context_processor
def getBookedList():
    def getbooklist(tsaddr):
        bookedList = reservedTsList.countTsReservationList(tsaddr)
        return bookedList
    return dict(getbooklist=getbooklist)

def relocateReservedTS():    
    if (datetime.datetime.now().minute % 5) == 0:
        #check if the relcating correctly
        for relocatedTs in relocatedTsList:
            temp = TSList.query.filter_by(tsAddress = relocatedTs[0]).first()
            if temp.tasAddress != relocatedTs[1]:
                #if ts is not belongs to reserved tas, relocate again
                modifyThread = Process(target=tasmodification, args=(relocatedTs[0], temp.tasAddress, relocatedTs[1]))
                modifyThread.start()
                #tasmodification(relocatedTs[0], temp.tasAddress, relocatedTs[1])

        relocateTSList = reservedTsList.display_list()
        fromTAS = ""
        for element in relocateTSList:
            print(element[2])
            if element[2] == True:
                relocatedTsList.append((element[0], element[1])) #ts addr, tas addr
                #locking(element[0])
            else:
                #unlocking(element[0])
                relocatedTsList.remove((element[0], element[1]))

            fromTAS = tsList[element[0]]['tas']
            modifyThread = Process(target=tasmodification, args=(element[0], fromTAS, element[1]))
            modifyThread.start()
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
    threading.Timer(20, relocateReservedTS).start()

relocateReservedTS()