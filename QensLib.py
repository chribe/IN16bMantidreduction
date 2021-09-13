from mantid.simpleapi import *
import numpy as np
# load FWS
def readFWS(runs,name,Observable='sample.temperature'):
    IndirectILLReductionFWS(
        OutputWorkspace=name+'_FWS',
        Run=runs,
        MapFile="IN16B_Grouping_Si111.xml",
        Analyser="silicon",
        Reflection="111",
        SpectrumAxis='Q',
        Observable=Observable,
        SortXAxis=True,
        DiscardSingleDetectors=False
    )
    Transpose(InputWorkspace=name+'_FWS_q',OutputWorkspace=name+'_FWS_q')

def readQENS(runs,name,Bin=None,UnmirrorOption=7,MapFile="IN16B_Grouping_Si111.xml"):
    try:
        IndirectILLReductionDIFF(SampleRuns=runs.replace(',','+'),
            OutputWorkspace=name+ '_diff',
            Transpose=True,
            Sum=True)
        Rebin(name+ '_diff', Params=0.02, OutputWorkspace=name+ '_diff')
        Divide(LHSWorkspace=name+ '_diff',
            RHSWorkspace='vana_diff',
            OutputWorkspace=name+ '_diff_norm')
        SaveNexus( name + '_diff_norm', name + '_diff_norm.nxs')
    except:
        print('skipping Diffraction')
    IndirectILLReductionQENS(
        OutputWorkspace=name+ '_QENS',
        Run=runs,
        AlignmentRun="341667",
        MapFile=MapFile,
        Analyser="silicon",
        Reflection="111",
        UnmirrorOption=UnmirrorOption,
        SpectrumAxis='Q',
        SumRuns=True,
        CropDeadMonitorChannels=False,
        DiscardSingleDetectors=False
   )
   
    for ws in mtd[name+ '_QENS'+'_q']:
        ws.setDistribution(True)
   
    if Bin:
        Rebin(InputWorkspace=name+ '_QENS'+'_q', OutputWorkspace=name+ '_QENS'+'_q', Params=Bin)

    SumSpectra(InputWorkSpace=name+ '_QENS'+'_q',OutputWorkspace=name+ '_QENS'+'_sum',ListOfWorkspaceIndices="2-15")
    NormaliseSpectra(InputWorkSpace=name+ '_QENS'+'_sum',OutputWorkspace=name+ '_QENS'+'_sum_norm')

    Integration(InputWorkspace=name+ '_QENS'+'_q',OutputWorkspace=name+ '_QENS'+'_integral')
    Transpose(InputWorkspace=name+ '_QENS'+'_integral',OutputWorkspace=name+ '_QENS'+'_integral')


# QENS
def readBATS(runs,name,Bin=0.6e-3,EMin=None,EMax=None,
             epp=None,eppOut=None):
    # Create a workspace containing some centered data for alignment.
#    CenteredGaussian = CreateSampleWorkspace(Function='User Defined',
#                               WorkspaceType='Histogram',
#                               UserDefinedFunction="name=Gaussian, PeakCentre=0, Height=10, Sigma=0.3",
#                               NumBanks=19, BankPixelWidth=1,
#                               XUnit='DeltaE', XMin=0, XMax=7, BinWidth=0.099)             
    map = "IN16B_Grouping_BATS_cycle211.xml"
    IndirectILLEnergyTransfer(Run=runs)
    IndirectILLEnergyTransfer(
        MapFile=map,
        OutputWorkspace=name,
        Run=runs, 
        ElasticPeakFitting='FitAllPixelGroups',
        MonitorCutoff=0.5,
        SpectrumAxis='Q',
        InputElasticChannelWorkspace=epp,
        OutputElasticChannelWorkspace=eppOut,
        GroupDetectors=False
    )
    
    CropWorkspace(InputWorkspace=name, OutputWorkspace=name, Xmin=EMin, XMax=EMax)
    if Bin:
        Rebin(InputWorkspace=name, OutputWorkspace=name, Params=Bin)
    GroupDetectors(InputWorkspace=name, OutputWorkspace=name+'_grouped', MapFile=map)
    ConvertSpectrumAxis(
        InputWorkspace=name+'_grouped',
        OutputWorkspace=name+'_grouped',
        Target='ElasticQ',
        EMode='Indirect',
        EFixed=2.080)
#    MatchPeaks(InputWorkspace=name+'_grouped',OutputWorkspace=name+'_matched',InputWorkspace2=CenteredGaussian)
    table=FindPeaks(InputWorkspace=name+'_grouped',PeakPositions=[0,-0.009])
#    CloneWorkspace(InputWorkspace=name+'_grouped',OutputWorkspace=name+'_centered')
#    UnGroupWorkspace(table)
#    offsets = mtd['table_1']
#    WS  = mtd[name+'_grouped']
#    cWS = mtd[name+'_centered']
#    print(cWS[0].id(),cWS[0].getName(),cWS[0].axes())
#    xaxis=cWS[0].getAxis(0)
#  #  y=WS[0].readY()
#  #  print(np.shape(y))
#    for hiq,_ in enumerate(np.arange(19)):
#        if hiq<3:
#           Offset=offsets.row(2*hiq)["centre"]
#        else:
#            Offset=offsets.row(2*hiq+1)["centre"]
##        y[:,hiq] = WS[0].readY(hiq) + Offset
# #       print(y.max(), np.shape(y))
##        xaxis.setValue(xaxis[hiq,:]-Offset)
##    cWS[0].replaceAxis(1, xaxis)
#         #ScaleX(InputWorkspace=name+'_grouped',OutputWorkspace=name+'_centered',Operation='Add',Factor=-Offset,IndexMin=hiq,IndexMax=hiq+1)
    SumSpectra(InputWorkSpace=name+'_grouped',OutputWorkspace=name+'_sum',StartWorkspaceIndex=3)

def MergeLogBook(LogBook,runnumbername='Numor',tobechecked=[]):
    tobechecked=tobechecked+['Type']
    Protocol={}
    print(LogBook.keys())
    for key in LogBook.keys():
        Protocol.update({key:[]})
    merged=np.zeros(len(LogBook[runnumbername]))
    for num,_ in enumerate(merged):
        if merged[num]==0:
            merged[num]=1
            for key in LogBook.keys():
                Protocol[key].append(LogBook[key][num])
            idx=np.ones(len(LogBook[runnumbername]))
            for num1,_ in enumerate(merged):
                for param in tobechecked:
                    if LogBook[param][num]!=LogBook[param][num1]:
                       idx[num1]=0
            for num1,_ in enumerate(merged):
                if num1 > num and idx[num1]==1:
                    merged[num1]=1
                    Protocol[runnumbername][-1]=" ".join((Protocol[runnumbername][-1],',',LogBook[runnumbername][num1]))
    return Protocol

def RemoveFromProtocol(Protocol,index):
    for key in Protocol.keys():
        indices=index
        for hi in index:
            Protocol[key].pop(max(indices))
            indices.remove(max(indices))
    return Protocol

def compareRuns(SampleName,entry,MeasureingType):
    if MeasureingType=='FWS':
        WS=mtd[SampleName]
        if type(WS) == mantid.dataobjects._dataobjects.Workspace2D:
            run=WS.getRun()
            RL=run.get('ReducedRunsList')
            runlist=RL.value.split(',')
        else:
            runlist=[]
            for hi,_ in enumerate(WS):
                run=WS[hi].getRun()
                RL=run.get('ReducedRunsList')
                runlist=runlist+RL.value.split(',')
        boolean=0
        Runlist=[int(i) for i in runlist]
        Entry=entry.split(',')
        Entrylist=[int(i) for i in Entry]
        for rn in Entrylist:
            if rn not in Runlist:
                boolean=1
                print('not yet included:' + str(rn))
    else:
        WS=mtd[SampleName]
        if type(WS) == mantid.dataobjects._dataobjects.Workspace2D:
            run=WS.getRun()
            RL=run.get('run_number')
            runlist=RL.value.split(',')
        else:
            runlist=[]
            for hi,_ in enumerate(WS):
                run=WS[hi].getRun()
                RL=run.get('run_number')
                runlist=runlist+RL.value.split(',')
        boolean=0
        Runlist=[int(i) for i in runlist]
        Entry=entry.split(',')
        Entrylist=[int(i) for i in Entry]
        for rn in Entrylist:
            if rn not in Runlist:
                boolean=1
                print('not yet included:' + str(rn))
    return boolean
    
def determineMeasurementType(LogBook):
    MeasurementType=[None] * len(LogBook['Profile'])
    for num,val in enumerate(LogBook['Profile']):            
        if "".join(val.split())=='sine' and float(LogBook['dE(ueV)'][num])!=0:
            MeasurementType[num]='QENS'
        else:
            MeasurementType[num]='FWS'
    LogBook.update({'Type':MeasurementType})
    return LogBook
    
def ChangeTitle(Logbook,ListofRunnumbers,NewTitle):
    for num,val in enumerate(Logbook['Numor']):
        if int(val) in ListofRunnumbers:
            if NewTitle[0]=='+':
                Logbook['Subtitle'][num]=Logbook['Subtitle'][num]+NewTitle[1:-1]
            else:
                Logbook['Subtitle'][num]=NewTitle
    return Logbook