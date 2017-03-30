from __future__ import print_function
from paramiko import ssh_exception as ssh_err
from multiprocessing.dummy import Pool as ThreadPool
import paramiko
import time

# Workers are waiting to do work here
pool = ThreadPool(4)

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
    username = 'ansible'
    password = 'ansible'
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password, look_for_keys=False,
                    allow_agent=False, timeout=5)
        print("SSH connection established to {0}".format(host))
        remote_shell = ssh.invoke_shell() # need shell for cisco devices
        disable_paging(remote_shell)
        # send enter key
        remote_shell.send("\n")
        # send command + enter key
        remote_shell.send('show running-config | include ^line vty|transport input' + '\n')
        # Wait for the command to complete
        time.sleep(8)
        output = remote_shell.recv(65000)
        if not 'ssh' in output:
            print('vulnerable')
        #print(output)
        #return output
    except (ssh_err.BadHostKeyException, ssh_err.AuthenticationException,
            ssh_err.SSHException, ssh_err.socket.error) as e:
        print("Could not invoke command on remote device because of the following error: {0}".format(e))


if __name__ == '__main__':
    hosts = ['172.16.1.46', '172.16.1.47', '172.16.1.48', '172.16.1.49']
    # run threads in parallel with the help of pool and map
    results = pool.map(run_cmd, hosts)
    # close the pool and wait for the work to finish
    # join blocks the calling thread until everything is finished
    # then other code can run below
    pool.close()
    pool.join()

