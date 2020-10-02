#!/usr/bin/env python
import os,re,sys,argparse,copy,argparse
from collections import OrderedDict
from MyaData import MyaData
from MyaFcup import MyaFcup
from CcdbUtil import *
#
# Use MYA EPICS archive to get Faraday cup offset, beam blocker attenuation,
# and half-wave plate status for CCDB.
#

cli=argparse.ArgumentParser(description='Extract fcup/hwp info from Mya archive for CCDB.')
cli.add_argument('start',help='start date (YYYY-MM-DD_HH:MM:SS)',type=str)
cli.add_argument('end',help='end date (YYYY-MM-DD_HH:MM:SS)',type=str)
args=cli.parse_args(sys.argv[1:])

# mya date format: (Y-M-D_H:M:S, with fixed widths:)
fmt='^\d\d\d\d-\d\d-\d\d_\d\d:\d\d:\d\d$'

mm=re.match(fmt,args.start)
if mm is None: cli.error('Invalid start date format: '+args.start)
mm=re.match(fmt,args.end)
if mm is None: cli.error('Invalid end date format: '+args.end)

print('Start:   '+args.start)
print('End:     '+args.end)

# User-defined: 
#start,end='2019-12-01 00:00:00','2019-12-18 00:00:00'#,0

# Note, with fcup scaler at ~1 kHz/nA, and beam stopper attenuation of 10X,
# then at 10 nA a 10 Hz offset is ~1% error on beam charge.  Normally the
# beam stopper would be OUT at 10 nA, or ~0.1% error per 10 Hz offset.  So
# we choose a conservative deadband of 10 Hz, sufficient for all cases.
fcup_offset_deadband=10

myaData = MyaData(args.start,args.end)
myaData.addPv('B_DAQ:run_number')
myaData.addPv('MBSY2C_energy')
myaData.addPv('fcup_offset',2)
myaData.addPv('beam_stop',50)
myaData.addPv('IGL1I00OD16_16')

runData=OrderedDict()
badEnergies=[]
previous=None

for x in ['fcup2ccdb.sh','hwp2ccdb.sh','hwp-data','fcup-data']:
  if os.path.exists(x):
    sys.exit('ERROR:  Output already Exists:  '+x)

# Load all data from MYA archive, ignore invalids,  apply deadbands,
# and register changes:
for myaDatum in myaData.get():

  current = MyaFcup(myaDatum)

  # if data invalid, assume it's the same as the previous:
  if current.atten is None:
    if current.stopper is not None:
      badEnergies.append(current)
    current.atten=previous.atten
  if current.run is None:
    current.run=previous.run
  if current.hwp is None:
    current.hwp=previous.hwp

  changed=False

  # check if attenuation changed:
  if current.atten is not None:
    if previous is None or previous.atten is None:
      changed=True
    elif abs(current.atten-previous.atten) > 0.01:
      changed=True

  # check if fcup_offset changed:
  if current.offset is not None:
    if previous is None or previous.offset is None:
      changed=True
    elif abs(current.offset-previous.offset) > 2:
      changed=True

  # check if hwp changed:
  if previous is None or current.hwp != previous.hwp:
    changed=True

  # if data changed, append the data for this run:
  if changed:
    if current.run not in runData:
      runData[current.run]=[]
    runData[current.run].append(current)

  # update the previous values:
  previous=current

# print any unknown beam energies:
if len(badEnergies)>0:
  print('\nIgnored Invalid Beam Energies:::::::::::::::::::')
  for xx in badEnergies:  print(xx)

# print all registered changes:
print('\nData:::::::::::::::::::::::::::::::::::::::')
for run,data in runData.items():
  for datum in data: print(datum)

def getOffsetAverage(data):
  offsets = [ datum.offset for datum in data ]
  return sum(offsets) / len(offsets)

hwps,offsets,attens=[],[],[]

# register hwp changes:
tmp = copy.deepcopy(runData)
firstRun,firstData = tmp.popitem(False)
while len(tmp)>0:
  lastRun,lastData = tmp.popitem(False)
  if firstData[len(firstData)-1].hwp != lastData[0].hwp or \
      firstData[0] != lastData[0].hwp or \
      len(tmp)==0:
    hwps.append(HwpCcdbEntry(firstRun,lastRun-1,{'hwp':firstData[0].hwp}))
    firstRun,firstData = lastRun,lastData

# register attenuation changes:
tmp = copy.deepcopy(runData)
firstRun,firstData = tmp.popitem(False)
while len(tmp)>0:
  lastRun,lastData = tmp.popitem(False)
  if abs(firstData[len(firstData)-1].atten-lastData[0].atten)>0.1 or \
      abs(firstData[0].atten-lastData[0].atten)>0.1 or \
      len(tmp)==0:
    attens.append(FcupCcdbEntry(firstRun,lastRun-1,{'atten':firstData[0].atten}))
    firstRun,firstData = lastRun,lastData

# register offset changes, with a running-average:
tmp = copy.deepcopy(runData)
firstRun,firstData = tmp.popitem(False)
while len(tmp)>0:
  lastRun,lastData = tmp.popitem(False)
  firstOffset = getOffsetAverage(firstData)
  lastOffset = getOffsetAverage(lastData)
  if abs(lastOffset-firstOffset) > fcup_offset_deadband or len(tmp)==0:
    offsets.append(FcupCcdbEntry(firstRun,lastRun-1,{'offset':round(firstOffset,1)}))
    firstRun,firstData = lastRun,lastData

# set last change's upper run limit to infinity:
offsets[len(offsets)-1].runMax=None
attens[len(attens)-1].runMax=None
hwps[len(hwps)-1].runMax=None

def findCcdbEntry(run,entries):
  for entry in entries:
    if entry.contains(run):
      return entry
  return None

print('\nFaraday Cup Offsets::::::::::::::::::::::::')
for offset in offsets: print(offset)
print('\nBeam Blocker Attenuations::::::::::::::::::')
for atten in attens: print(atten)
print()
print('\nHalf Wave Plates:::::::::::::::::::::::::::')
for hwp in hwps: print(hwp)
print()
print()

fcmd=open('fcup2ccdb.sh','w')
tmp = copy.deepcopy(runData)
runStart=tmp.keys()[0]
previous=None
while len(tmp.keys())>0:
  run,data = tmp.popitem(False)
  offset,atten=None,None
  for ii in range(len(offsets)):
    if offsets[ii].contains(run):
      offset=offsets[ii].data
      break
  for ii in range(len(attens)):
    if attens[ii].contains(run):
      atten=attens[ii].data
      break
  data=dict(offset,**atten)
  if previous is not None and previous!=data or len(tmp.keys())==0:
    f=FcupCcdbEntry(runStart,run-1,previous)
    if len(tmp.keys())==0:
      f.runMax=None
    runStart=run
    print(f)
    f.writeFile(directory='./fcup-data')
    fcmd.write(f.getCommand()+'\n')
  previous=data

fcmd.close()
fcmd=open('hwp2ccdb.sh','w')
tmp = copy.deepcopy(runData)
runStart=tmp.keys()[0]
previous=None
while len(tmp.keys())>0:
  run,data = tmp.popitem(False)
  hwp=None
  for ii in range(len(hwps)):
    if hwps[ii].contains(run):
      hwp=hwps[ii].data
      break
  data=hwp
  if previous is not None and previous!=data or len(tmp.keys())==0:
    f=HwpCcdbEntry(runStart,run-1,previous)
    if len(tmp.keys())==0:
      f.runMax=None
    runStart=run
    print(f)
    f.writeFile(directory='./hwp-data')
    fcmd.write(f.getCommand()+'\n')
  previous=data

print()

