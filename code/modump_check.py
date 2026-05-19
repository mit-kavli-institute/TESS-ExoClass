# -*- coding: utf-8 -*-
"""
Check for events falling near momentum dumps

AUTHOR: Christopher J. Burke
"""

import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import numpy as np
import pickle
from gather_tce_fromdvxml import tce_seed
import os
from subprocess import Popen, PIPE
import math
import h5py
from statsmodels import robust
from pgmcmc import pgmcmc_ioblk, pgmcmc_setup
from pgmcmc import pgmcmc_run_mcmc, pgmcmc_run_minimizer
import matplotlib.pyplot as plt
import argparse
from tec_used_params import tec_use_params

def make_data_dirs(prefix, sector, epic):
    secDir = 'S{0:02d}'.format(sector)
    localDir = os.path.join(prefix,secDir)
    if not os.path.exists(localDir):
        os.mkdir(localDir)
    epcDir = '{0:04d}'.format(int(math.floor(epic/1000.0)))
    localDir = os.path.join(prefix,secDir,epcDir)
    if not os.path.exists(localDir):
        os.mkdir(localDir)
    return localDir


def phaseData(t, per, to):
    """Phase the data at period per and centered at to
       INPUT:
         t - time of data
         per - period to phase time data period and t should
               be in same units
         to - epoch of phase zero
       OUTPUT:
         phi - data phased running from -0.5<phi<=0.5
     """
    phi = np.mod(t - to, per) / per
    phi = np.where(phi > 0.5, phi - 1.0, phi)
    return phi

def idx_filter(idx, *array_list):
    new_array_list = []
    for array in array_list:
        new_array_list.append(array[idx])
    return new_array_list



if __name__ == '__main__':
    # Parse the command line arguments for multiprocessing
    # With Gnu parallel with 13 cores
    # seq 0 12 | parallel --results modump_check_results python modump_check.py -w {} -n 13
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", type=int, default=0,
                        help="Worker ID Number 0 through nWrk-1")
    parser.add_argument("-n", type=int, default=1,
                        help="Number of Workers")
    args = parser.parse_args()
    wID = int(args.w)
    nWrk = int(args.n)

    tp = tec_use_params()
    #  Directory storing the ses mes time series
    sesMesDir = '/pdo/users/cjburke/spocvet/{0}'.format(tp.tecdir)
    SECTOR = tp.sector

    fileOut = 'spoc_modump_{0}.txt'.format(tp.tecfile)
    if nWrk > 1:
        fileOut = 'spoc_modump_{0}_w{1:d}.txt'.format(tp.tecfile, wID)
    fom = open(fileOut, 'w')
    vetFile = 'spoc_fluxtriage_{0}.txt'.format(tp.tecfile)
    #vetFile = 'junk.txt'
    tceSeedInFile = '{0}_tce.h5'.format(tp.tecfile)

    # cadence number time mapping has momentum dump flags in it
    # It is generated in dvts_bulk_resamp.py
    dataBlock = np.genfromtxt('cadnoVtimemap.txt', dtype=['i4','f8','i4','i4','i4'])
    cadmap = dataBlock['f0']
    timemap = dataBlock['f1']
    momdump = dataBlock['f3']
    idx = np.where(momdump == 1)[0]
    bdTime = timemap[idx]
    
    # Load the tce data h5
    tcedata = tce_seed()
    all_tces = tcedata.fill_dset_from_hd5f(tceSeedInFile)

    alltic = np.array(all_tces['epicId'], dtype=np.int64)
    allpn = np.array(all_tces['planetNum'], dtype=int)
    allatvalid = np.array(all_tces['at_valid'], dtype=int)
    allrp = np.array(all_tces['at_rp'])
    allrstar = np.array(all_tces['rstar'])
    alllogg = np.array(all_tces['logg'])
    allper = np.array(all_tces['at_period'])
    alltmags = np.array(all_tces['tmag'])
    allmes = np.array(all_tces['mes'])
    allsnr = np.array(all_tces['at_snr'])
    alldur = np.array(all_tces['at_dur'])
    allsolarflux = np.array(all_tces['at_effflux'])
    allatdep = np.array(all_tces['at_depth'])
    allatepoch = np.array(all_tces['at_epochbtjd'])
    alltrpvalid = np.array(all_tces['trp_valid'])
    allatrpdrstar = np.array(all_tces['at_rpDrstar'])
    allatrpdrstare = np.array(all_tces['at_rpDrstar_e'])
    allatadrstar = np.array(all_tces['at_aDrstar'])

    # Load the  flux vetting
    dataBlock = np.genfromtxt(vetFile, dtype=[int,int,int,'S1'])
    fvtic = dataBlock['f0']
    fvpn = dataBlock['f1']
    fvvet = dataBlock['f2']
    
    vet_lookup = {(int(fvtic[i]), int(fvpn[i])): int(fvvet[i])
                  for i in range(len(fvtic))}
    allvet = np.array([vet_lookup.get((int(alltic[i]), int(allpn[i])), 0)
                       for i in range(len(allpn))], dtype=allpn.dtype)
    # only keep tces with both valid dv and trapezoid fits
    # and flux vetted pass
    idx = np.where((allatvalid == 1) & (alltrpvalid == 1) & (allsolarflux > 0.0) & \
                   (allvet == 1))[0]
    
    alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
            allatrpdrstar, allatrpdrstare, allatadrstar = idx_filter(idx, \
            alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
            allatrpdrstar, allatrpdrstare, allatadrstar)
    # These lines can be used for debugging
    #idx = np.where((alltic == 101955023))[0]
    #alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
    #        allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
    #        allatrpdrstar, allatrpdrstare, allatadrstar = idx_filter(idx, \
    #        alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
    #        allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
    #        allatrpdrstar, allatrpdrstare, allatadrstar)
            
    # Recalculate MES after removing momentum dump impacted events
    for i, curTic in enumerate(alltic):
        if np.mod(i, nWrk) != wID:
            continue
        print('{:d} of {:d}'.format(i, len(alltic)))
        curPn = allpn[i]
        curDur = alldur[i]
        curDurDay = curDur/24.0
    
        fileInput = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_sesmes_{0:016d}_{1:02d}.h5d'.format(curTic,curPn))
        f = h5py.File(fileInput,'r')
        allCorr = np.array(f['allCorr'])
        allNorm = np.array(f['allNorm'])
        allTime = np.array(f['allTime'])
        allCadNo = np.array(f['allCadNo'])
        nBd = 0
        for j in range(len(allCorr)):
            curTime = allTime[j]
            tDiff = np.abs(curTime - bdTime)
            idx = np.where(tDiff < curDurDay)[0]
            if len(idx)>0:
                nBd = nBd + 1
        fracBd = float(nBd)/float(len(allCorr))
        #print('{0:d} {1:f}'.format(curTic, fracBd))

        
        fom.write('{:016d} {:02d} {:f}\n'.format( \
                      curTic, curPn, fracBd))

    fom.close()
