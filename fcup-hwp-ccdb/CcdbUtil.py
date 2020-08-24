import os

class RunRange:
  def __init__(self,runMin,runMax,data):
    self.runMin=runMin
    self.runMax=runMax
    self.data=data
  def setRunMin(self,runMin):
    self.runMin=runMin
    return self
  def setRunMax(self,runMax):
    self.runMax=runMax
    return self
  def contains(self,run):
    if self.runMin is not None and run<self.runMin:
      return False
    if self.runMax is not None and run>self.runMax:
      return False
    return True
  def __str__(self):
    return '%s-%s %s'%(str(self.runMin),str(self.runMax),self.data)

class CcdbEntry(RunRange):
  def __init__(self,runMin,runMax,data={},sector=0,layer=0,component=0):
    RunRange.__init__(self,runMin,runMax,data)
    self.prefix=None
    self.table=None
    self.sector=sector
    self.layer=layer
    self.component=component
  def getSLC(self):
    return '%d %d %d'%(self.sector,self.layer,self.component)
  def getFilename(self):
    return '%s_%s-%s.txt'%(self.prefix,str(self.runMin),str(self.runMax))
  def writeFile(self,directory=None):
    if directory is None: directory='.'
    if not os.access(directory,os.W_OK):
      os.makedirs(directory)
    with open(directory+'/'+self.getFilename(),'w') as f:
      f.write(self.getRow())
      f.close()
  def getCommand(self):
    cmd='ccdb -c mysql://clas12writer:geom3try@clasdb/clas12 add '+self.table+' '
    if self.runMin is not None:
      cmd+=str(self.runMin)
    cmd+='-'
    if self.runMax is not None:
      cmd+=str(self.runMax)
    cmd+=' '+self.getFilename()
    return cmd

class FcupCcdbEntry(CcdbEntry):
  def __init__(self,runMin,runMax,data={'offset':None,'atten':None}):
    if 'slope' not in data:
      data['slope']=906.2
    CcdbEntry.__init__(self,runMin,runMax,data)
    self.prefix='fcup'
    self.table='runcontrol/fcup'
  def setSlope(self,slope):
    self.data['slope']=slope
  def setOffset(self,offset):
    self.data['offset']=offset
  def setAttenuation(self,atten):
    self.data['atten']=atten
  def getRow(self):
    return '%s %.2f %.2f %.5f'%(self.getSLC(),\
        self.data['slope'],self.data['offset'],self.data['atten'])

class HwpCcdbEntry(CcdbEntry):
  def __init__(self,runMin,runMax,data={'hwp':None}):
    CcdbEntry.__init__(self,runMin,runMax,data)
    self.prefix='hwp'
    self.table='runcontrol/hwp'
  def setHWP(self,hwp):
    self.data['hwp']=hwp
  def getRow(self):
    return '%s %d'%(self.getSLC(),self.data['hwp'])

if __name__ == '__main__':

  f=FcupCcdbEntry(4013,4099)
  f.setSlope(906.2)
  f.setOffset(120.1)
  f.setAttenuation(10.1)
  f.writeFile()
  print f

  h=HwpCcdbEntry(1234,2345)
  h.setHWP(-1)
  print h

