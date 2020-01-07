import subprocess, paramiko, time, socket

def connectToSsh(ip,usn,pwd):
    i = 0
    while i!=2:
        try:
            ssh = paramiko.SSHClient()
            print("\ncalling paramiko")
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())           
            print("\nRemote Login to Unix Server: " + ip + " successful.")
            ssh.connect(ip,username=usn,password=pwd)
            print("\ntrying to connect")
            shell = ssh.invoke_shell(width=120,height=80)
            shell.keep_this = ssh
            return shell
        except paramiko.AuthenticationException:
            print( "Authentication failed when connecting " + ip + ".")
        except:
            print( "Could not SSH to " + ip + ", waiting for it to start.")
            i+=1
            time.sleep(2)


USERNAME = "cfguser"
PASSWORD = "cfguser"

print (("*")*100)
HOST = "10.140.92.130"
TAS = "10.140.92.212"

shell = connectToSsh(HOST, USERNAME, PASSWORD)
if shell != None:
	shell.send('su\n')
	time.sleep(2)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('spirent\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('ipcfg\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('yes\n')
	time.sleep(13)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send(TAS + '\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)

time.sleep(30)
shell = connectToSsh(HOST, USERNAME, PASSWORD)
if shell != None:
	shell.send('su\n')
	time.sleep(2)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('spirent\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)
	shell.send('/home/spcoast/bin/tsd.sh start\n')
	time.sleep(1.5)
	rcv = shell.recv(1024)
	print (rcv)


