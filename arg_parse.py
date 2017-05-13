from __future__ import print_function
from paramiko import ssh_exception as ssh_err
from multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime
import paramiko
import time
import getpass
import argparse
import csv


# Workers are waiting to do work here
pool = ThreadPool(4)

time = datetime.now()
dest_csv_file = 'ssh_compliance_report_{0}_{1}_{2}.csv'.format(time.month, time.day, time.year)
parser = argparse.ArgumentParser()
parser.add_argument('-s', dest='source_filename', type= str, help='source csv filename', required=True)
parser.add_argument('-u', dest='username', type= str, help='username', required=True)
parser.add_argument('-c', dest='command', type= str, help='command to run', required=True)
args = parser.parse_args()
password = getpass.getpass("Enter the Password: ")

def get_csv_info(source_csv_file):
    ''' create a list of lists from the source csv file '''
    with open(source_csv_file, 'r') as f:
        csv_reader = csv.DictReader(f, delimiter=',')
        hosts = list()
        for row in csv_reader:
            pair = [row['name'], row['ipaddress']]
            hosts.append(pair)
    return(hosts)

def post_csv_info(dest_csv_file, hosts):
    ''' append telnet status to the host list and write to new csv '''
    with open(dest_csv_file, 'w', newline='') as f:
        fieldnames = ['name', 'ipaddress', 'telnet']
        csv_writer = csv.DictWriter(f, delimiter=',', fieldnames=fieldnames)
        csv_writer.writeheader()
        for host in hosts:
            print(host)
            csv_writer.writerow({'name': host[0], 'ipaddress': host[1], 'num_of_eth_cards': host[2]})

def disable_paging(remote_shell):
    '''Disable paging on a Cisco router'''
    remote_shell.send("terminal length 0\n")
    time.sleep(1)
    # Clear the buffer on the screen
    output = remote_shell.recv(1000)
    return output

def run_cmd(host):
    ''' Instantiate SSHClient object. Disable strict hostkey checking. Invoke the shell.
        Run the command provided and receive the output. '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host[1], username=args.username, password=password, look_for_keys=False,
                    allow_agent=False, timeout=5)
        print("SSH connection established to {0}".format(host[0]))
        remote_shell = ssh.invoke_shell() # need shell for cisco devices
        disable_paging(remote_shell)
        # send enter key
        remote_shell.send("\n")
        # send command + enter key
        remote_shell.send(args.command)
        # Wait for the command to complete
        time.sleep(8)
        output = remote_shell.recv(65000)
        host.append('Hello')
        #print(output)
        #return output
    except (ssh_err.BadHostKeyException, ssh_err.AuthenticationException,
            ssh_err.SSHException, ssh_err) as e:
        host.append('Hello')
        print("Could not invoke command on remote device because of the following error: {0}".format(e))


if __name__ == '__main__':
    #hosts = ['10.8.79.250']
    hosts = get_csv_info(args.source_filename)
    print(hosts)
    # run threads in parallel with the help of pool and map
    results = pool.map(run_cmd, hosts)
    # close the pool and wait for the work to finish
    # join blocks the calling thread until everything is finished
    # then other code can run below
    pool.close()
    pool.join()
    post_csv_info(dest_csv_file, hosts)
