#!/usr/bin/python3

#PYTHON SCRIPT TO MONITOR TRAFFIC NETWORKS WITH SNMP AGENT AND RRDTOOL

#IMPORT
import sys
import time
import rrdtool
import os.path
import subprocess
from time import sleep
from easysnmp import Session, snmp_get



#PARAMETERS CHECK
community = input('Enter the community --> ')
hostname = input('Enter hostname --> ')
version = 2

if (len(community)==0 or len(hostname)==0):
	print('Invalid parameters ... Try again!\n')
	sys.exit()


################################################################################################################################


session = Session(hostname=hostname,community=community,version=version) #SNMP SESSION


#INTERFACES
num_if = int(session.get('ifNumber.0').value) #IF-MIB::ifNumber.0
print(f'\nYou have {num_if} network interfaces:')

for i in range(num_if+1):
	ifname = session.get(f'ifName.{i}').value #IF-MIB::ifName
	if(i != 0):
		print(f'{i} --> {ifname}') 

interface = input('\nEnter the index of the interface that you want to monitor --> ')

if((int(interface) < 1) or (int(interface) > num_if)):
	print('\nWrong index ... Try again!\n')
	sys.exit()
	
name = session.get(f'ifName.{interface}').value
new_file = name + '.rrd' #name of file.rrd 

################################################################################################################################

#CREATING FILE.RRD AND TWO RRAs
#FIRST RRA KEEPS LAST-HOUR RAW DATA, SO IT NEEDS 360 CELLS (3600/10)
#SECOND RRA KEEPS AVERAGE PER MINUTE FOR A WEEK, SO IT NEEDS 6 (60/10) RAW DATA TO DO THE AVERAGE AND 10.080 CELLS 

filename = new_file 
step = 10
attesa_max = step*2
min_val = 0
max_val = 'U'

tempo1 = 3600
celle_rra1 = int(tempo1/step) #360 last-hour cells

tempo2 = 60 
valori = int(tempo2/step) 
celle_rra2 = 7*24*60 #average per minute for a week, 10.080 cells


#Check if file.rrd has been already created
if(os.path.isfile(f'{filename}') == False): 
	print(f'\nCreating new file {filename}\n')
	db = rrdtool.create(filename,'--step',str(step),f'DS:in:COUNTER:{attesa_max}:{min_val}:{max_val}',f'DS:out:COUNTER:{attesa_max}:{min_val}:{max_val}',f'RRA:AVERAGE:0.5:1:{celle_rra1}',f'RRA:AVERAGE:0.5:1:{celle_rra1}',f'RRA:AVERAGE:0.5:{valori}:{celle_rra2}',f'RRA:AVERAGE:0.5:{valori}:{celle_rra2}')
else:
	print(f'\n{filename} already exists\n')


################################################################################################################################

	
num_iter = 0
prec_in = 0
prec_out = 0

try:
	while(True):
		bit_input = 8*int(session.get(f'ifInOctets.{interface}').value) #IF-MIB::ifInOctets
		bit_out = 8*int(session.get(f'ifOutOctets.{interface}').value) #IF-MIB::ifOutOctets
		
		db = rrdtool.update(filename,'N:%s:%s' %(str(bit_input),str(bit_out)))

		#Inbound traffics (in Mbit) during last 10 seconds 
		diff_in = abs(prec_in - bit_input)
		bps_in = int(diff_in/step)
		mbps_in = round(bps_in/(2**20),3)
		prec_in = bit_input

		#Outbound traffics (in Mbit) during last 10 seconds 
		diff_out = abs(prec_out - bit_out)
		bps_out = int(diff_out/step)
		mbps_out = round(bps_out/(2**20),3)
		prec_out = bit_out
		
		#Bandwidth usage (in Mbps) during last 10 seconds
		tmp = int((diff_in + diff_out)/step)
		bandwidth = round(tmp/(2**20),3)

		print('\n' + time.ctime())
		print('------------ [TRAFFIC NETWORK] ------------')
		print(f'Inbound Traffic: {mbps_in} Mbps')
		print(f'Outbound Traffic: {mbps_out} Mbps')
		print(f'Bandwidth Usage: {bandwidth} Mbps')
		print('-----------------------------------------')
		
		sleep(step)
		
except KeyboardInterrupt:
	subprocess.call('clear',shell=True)
	ifname = session.get(f'ifName.{interface}').value
	print(f'\nStop monitoring on {ifname}\n')
	
	
	
	
	
	
	
