import math
from mantid.simpleapi import *
from importlib import reload
from mantid.api import WorkspaceGroup
import QensLib as QL
import numpy as np
reload(QL)
import os
import csv
# create logbook
cycle="213"
beamtime="exp_8-04-923"
try:
    os.remove("/net4/serdon/illdata/" + cycle + "/in16b/" + beamtime + "/processed/logbook.csv")
except:
    print('no logbook deleted')
try:
    os.system("./nxs_log.py " + cycle + " in16b " + beamtime +" -s /net4/serdon/illdata/" + cycle + "/in16b/" + beamtime + "/processed/logbook.csv")
    f=open("/net4/serdon/illdata/" + cycle + "/in16b/" + beamtime + "/processed/logbook.csv")
    f.close()
except:
    os.system('pip install pyyaml')
    os.system("./nxs_log " + cycle + " in16b " + beamtime +" -s /net4/serdon/illdata/" + cycle + "/in16b/" + beamtime + "/processed/logbook.csv")
expdir = "/net4/serdon/illdata/"+ cycle +"/in16b/" + beamtime + "/"

config.appendDataSearchDir(expdir + "/rawdata")
config.appendDataSearchDir(expdir + "/processed")
#config.appendDataSearchDir("/net4/serdon/illdata/211/in16b/internalUse/rawdata")
#config.appendDataSearchDir("/net4/serdon/illdata/211/in16b/exp_DIR-211/rawdata")

ConfigService.Instance().setString('defaultsave.directory', "/net4/serdon/illdata/" + cycle + "/in16b/" + beamtime + "/processed/reduced_data/")

#config.appendDataSearchDir("/net/in16b/users/data")
# readin logbook
Logbook={}
with open('/net4/serdon/illdata/' + cycle + '/in16b/' + beamtime + '/processed/logbook.csv', 'r') as csvfile:
    LogEntry=csv.DictReader(csvfile,delimiter=',')
    fields= LogEntry.fieldnames
    for field in fields:
        Logbook[field]=[]
    for row in LogEntry:
        for field in fields:
            Logbook[field].append(row[field])
# create Protocol
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Logbook=QL.determineMeasurementType(Logbook)
#add Type QENS
#Logbook["Type"]=[]
#for hi,_ in enumerate(Logbook[field]):
#   Logbook["Type"].append("QENS")
# -----------------------------------------
Bin = 0.1E-3
Emin = -0.145 # for BATS
Emax = 0.175
#############################################################
vanaQENSmin=341667
vanaQENSmax=341739
runnumberVan=str(vanaQENSmin) +':' + str(vanaQENSmax)
vanaEFWS=341740
#############################################################
try:
    QL.readFWS(str(vanaEFWS),'VanaEFWS')
except:
    print('no FWS Analysis possible')
try:
        IndirectILLReductionDIFF(SampleRuns=str(np.arange(vanaQENSmin,vanaQENSmax+1)).strip('[]').replace('\n','').replace(' ','+'),
            OutputWorkspace='vana_diff',
            Transpose=True,
            Sum=True)
        Rebin('vana_diff', Params=0.02, OutputWorkspace='vana_diff')
except:
        print('skipping Diffraction')
#SaveNexus( 'vana_QENS_q', 'Vanadiumfoiltotal3ginTueoutercyl 280.00.nxs')
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#Logbook=QL.ChangeTitle(Logbook,np.arange(321455,321464),"Buffer His-HCl D2O")
print('###############################################')
print(Logbook['Subtitle'][73])
print(len(Logbook['Profile']))
print(len(Logbook['dE(ueV)']))
print(Logbook['Numor'][73])
print('###############################################')
Protocol=QL.MergeLogBook(Logbook,tobechecked=['Subtitle'])#'TSet(K)'
print('###############################################')
print(Protocol['Subtitle'][1])
print(Protocol['Type'][1])
print(Protocol['Profile'][1])
print(Protocol['dE(ueV)'][1])
print(Protocol['Numor'][1])
print('###############################################')

Bin = 0.1E-3
hi=0
WSnames = mtd.getObjectNames()
for entrynum,entry in enumerate(Protocol['Numor']):
    SampleName="".join(Protocol['Subtitle'][entrynum].split())
    SampleName=SampleName.replace('/','_')
    print(SampleName)
    ext=Protocol['Type'][entrynum]
    print(entry)
    print(ext)
    if ((SampleName + '_'+ ext + '_q' not in WSnames) or (QL.compareRuns(SampleName + '_'+ ext + '_q',entry,ext))) : # check if data is already loaded and if it is up to date otherwise, load
        if ext=='BATS':#BATS
            QL.readBATS(entry,SampleName,Bin=Bin,EMin=Emin,EMax=Emax,epp='epp_lres4')
            SaveNexus( SampleName + '_grouped', SampleName + Protocol['TSet(K)'][entrynum] + '_BATS.nxs')
        elif ext=='QENS':#QENS
            #SampleName+=Protocol['TSet(K)'][entrynum]
            QL.readQENS(entry,SampleName)
            SaveNexus( SampleName + '_QENS_q', SampleName + '_QENS_q.nxs')
            SaveNexus( SampleName + '_diff', SampleName + '_diff.nxs')
        else:#FWS
            QL.readFWS(entry,SampleName)
            Transpose(SampleName +"_FWS_q",OUTPUTWORKSPACE=SampleName + "_FWS_transposed")
            SaveNexus(SampleName +"_FWS_q", SampleName + '_FWS_q.nxs')
            ws_group = WorkspaceGroup()
            mtd.add(SampleName +"_FWS_q_norm", ws_group)
            print('Workspace group created')
            for ws in mtd[SampleName +"_FWS_q"]:
                    Divide(LHSWorkspace=ws,RHSWorkspace='VanaEFWS_FWS_q',OutputWorkspace=ws.name()+'_norm')
                    UnGroupWorkspace(mtd[ws.name() +"_norm"])
                    ws_group.addWorkspace(mtd[ws.name() +"_norm_1"])
            SaveNexus(SampleName +"_FWS_q_norm", SampleName + '_FWS_q_norm.nxs')               
#                print('no normalization of the FWS')
            
#for entrynum,entry in enumerate(Protocol['Numor']):
#    #SampleName=Protocol['Subtitle'][entrynum]
#    #SampleName.replace(" ","_")
#    hi+=1
#    #SampleName="sample" + 
#    #print(SampleName)
#    if Protocol['Type'][entrynum]=='BATS':
#        QL.readBATS(entry,"sample "+ str(hi))
#    elif (Protocol['Profile'][entrynum]=='sine') and (float(Protocol['dE(ueV)'][entrynum])!=0):#QENS
#        QL.readQENS(entry,"sample "+ str(hi))
#    else:#FWS
#        QL.readFWS(entry,"sample "+ str(hi))
#        Transpose("sample "+ str(hi) +"_q",OUTPUTWORKSPACE="sample "+ str(hi) + " transposed")
#        SaveNexus(SampleName +"_FWS_q",expdir + 'processed/reduced_data/' + SampleName +"_FWS_q.nxs")
#        SaveNexus(SampleName +"_FWS_transposed",expdir + 'processed/reduced_data/' + SampleName +"_FWS_transposed.nxs")
#                
