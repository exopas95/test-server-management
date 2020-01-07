import threading
import Queue
import multiprocessing
from time import sleep

def myThread(name, q):
	i = 0
	while True:
		sleep(1)
		q.put(i)
		i += 1

def myProcess(name, nsec):
	print ("-----hello" + str(nsec) + "-----")
	sleep(nsec)




if __name__ == '__main__':
	BUF_SIZE = 10
	q = Queue.Queue(BUF_SIZE)

	#t = multiprocessing.Process(target=myProcess, args=("Process-1", 3))
	#t.start()
	#t.join()
	#print ("---- end of program -----")
	t = threading.Thread(target=myThread, args=("Thread-1", q))
	t.start()

	while True:
		num = q.get()
		print (str(num) + "has created!")
	print ("---- end of program -----")
