import os, shutil, resource
from time import sleep
from multiprocessing import Process, Value
from ipaddress import ip_network
from datetime import datetime


def subnet_ping(ip, counter):

    response = os.system("ping -c 2 " + str(ip) + "\n") #CLI to use to ping

    # ICMP returns 0 if ping is successful, if something else, a non-zero value will be returned
    if response == 0:
        print(ip, 'is up!', "\n")
        out = "%s is up! \n" %(ip)
        log_file(out)
        counter.value += 1
    else:
        print(ip, "is down or can't be pinged!", "\n")
        out = "%s is down or can't be pinged! \n" %(ip)
        log_file(out)


def log_file(info): #function for writing to logfile

    with open(log_file_name, 'a+') as f:
        f.write(info)




if __name__ == '__main__':

    # if mac set number of open files from default 256 to 10240 for this parent process and all subs
    if os.name == 'posix':
        resource.setrlimit(resource.RLIMIT_NOFILE, (10240, 10240))
        #print("Setting min/max file limit to 10240/10240...")

    #input = "10.0.0.0/30"
    input = str(input("Enter IPv4 subnet with CIDR. \nExample: 192.168.0.0/24 \nEnter Here: "))
    counter = Value('i', 0)  # shared counter for all processes to have access to increment
    dt = datetime.now()
    log_file_name = "ping_log.txt"
    archive_logfile_name = "logs_{}-{}-{}-{}-{}-{}.txt".format(dt.hour, dt.minute, dt.second, dt.month, dt.day, dt.year)
    archive_logfile_path = "Archive/%s" % (archive_logfile_name)
    counter.value = 0

    #remove old log file if it exists, create new archive folder if one doesn't exist, move old to archive
    if not os.path.exists('Archive'):
        os.mkdir('Archive')

    if os.path.exists(log_file_name):
        os.rename(log_file_name, archive_logfile_name)
        shutil.move(archive_logfile_name, archive_logfile_path)

    if "/" in input: #if CIDR in input, many ping processes

        ip_addr = list(ip_network(input).hosts())  # built-in ip recognizer creates a list based on CIDR input
        total_hosts = len(ip_addr)  # grab total number of hosts within the subnet to ping (length of list)
        processes = []  # create process queue for each ip to be pinged. Prob need to look into better management of this
        workers = [0 for x in range(50)]
        increment_ip = 0  # increment on index of ip_addr because a list is returned
        length_of_list = len(ip_addr)  # grab number of IPs - later you count down to 0

        try:
            while length_of_list > 0:

                if 0 not in workers:
                    workers = [0 for x in range(50)]

                for w in range(len(workers)):
                    p = Process(target=subnet_ping, args=(ip_addr[increment_ip], counter))
                    p.start()  # start the process
                    processes.append(p)  # add to list of workers available to run processes
                    workers.remove(0)
                    increment_ip += 1
                    length_of_list -= 1

                for p in processes:
                    p.join()  # calling process blocked until process who's join method is called terminates.
                              # used more or less for queuing. If join is not used all processes join immediately
                              # you can also specify an optional timeout in case waiting is too long

        except IndexError:
            pass

        if processes[-1].is_alive() == False:  # check to see if last process is alive
            sleep(15)
            print("%s of %s hosts could be pinged." % (counter.value, total_hosts))
            out_hosts = "\n%s of %s hosts could be pinged." % (counter.value, total_hosts)
            out_completed = "\nCompleted @ {}-{}-{}-{}-{}-{}.txt".format(dt.hour, dt.minute, dt.second, dt.month, dt.day,
                                                                       dt.year)
            log_file(out_completed)
        elif processes[-1].is_alive() == True:
            sleep(15) # figure out how to make this wait for all processes complete
            print("%s of %s hosts could be pinged." % (counter.value, total_hosts))
            out_hosts = "\n%s of %s hosts could be pinged." % (counter.value, total_hosts)
            out_completed = "\nCompleted @ {}-{}-{}-{}-{}-{}.txt".format(dt.hour, dt.minute, dt.second, dt.month, dt.day,
                                                                       dt.year)

            log_file(out_hosts)
            log_file(out_completed)
        else:
            print("Process is hung! Please quit program and restart.")


















