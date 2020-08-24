
from MyaData import MyaDatum

_BEAM_ENERGY_TOLERANCE=10  # MeV

#
# Beam blocker attenuation factor is dependent on beam energy.
# Here we hardcode the results of the attenuation measurements.
#
_ATTEN={}
_ATTEN[10604]= 9.8088
_ATTEN[10409]= 9.6930
_ATTEN[10339]= 9.6930  # unmeasured during BONuS, copied from 10409
_ATTEN[10389]= 9.6930  # unmeasured during BONuS, copied from 10409
_ATTEN[10197]= 9.6930  # bogus beam energy from ACC, actually 10339
_ATTEN[10200]= 9.96025
_ATTEN[ 7546]=14.89565
_ATTEN[ 6535]=16.283
_ATTEN[ 6423]=16.9726

class MyaFcup:
  beamStopThreshold=10
  runNumberMax=2e4
  def __init__(self,myaDatum):
    if not isinstance(myaDatum,MyaDatum):
      sys.exit('MyaFcup requires a MyaDatum')
    self.date = myaDatum.date
    self.time = myaDatum.time
    try:
      self.run = int(myaDatum.getValue('B_DAQ:run_number'))
      if self.run > self.runNumberMax:
        self.run=None
    except ValueError:
      self.run = None
    try:
      self.energy = float(myaDatum.getValue('MBSY2C_energy'))
    except ValueError:
      self.energy = None
    try:
      # convert to -1/0/+1=IN/UDF/OUT scheme:
      self.hwp = int(myaDatum.getValue('IGL1I00OD16_16'))
      if   self.hwp == 1: self.hwp = -1
      elif self.hwp == 0: self.hwp = 1
      else:               self.hwp = 0
    except ValueError:
      self.hwp = None
    try:
      self.offset = float(myaDatum.getValue('fcup_offset'))
    except ValueError:
      self.offset = None
    try:
      self.stopper = float(myaDatum.getValue('beam_stop'))
    except ValueError:
      self.stopper = None
    self.atten = self.getAttenuation()
  def getAttenuation(self):
    if self.energy is None:
      return None
    if self.stopper is None:
      return None
    if self.stopper < self.beamStopThreshold:
      return 1.0
    for e in _ATTEN.keys():
      if abs(e-self.energy)<self._BEAM_ENERGY_TOLERANCE:
        return _ATTEN[e]
    return None
  def __str__(self):
    s='%10s %10s'%(self.date,self.time)
    if self.run is None:     s+=' %5s'%self.run
    else:                    s+=' %5d'%self.run
    if self.energy is None:  s+=' %8s'%self.energy
    else:                    s+=' %8.2f'%self.energy
    if self.stopper is None: s+=' %6s'%self.stopper
    else:                    s+=' %6.3f'%self.stopper
    if self.atten is None:   s+=' %8s'%self.atten
    else:                    s+=' %8.5f'%self.atten
    if self.offset is None:  s+=' %6s'%self.offset
    else:                    s+=' %5.1f'%self.offset
    s+=' %s'%self.hwp
    return s

