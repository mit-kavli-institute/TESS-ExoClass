This document describes the procedure for running TEC on a SPOC run.

# Environment

Make 6 terminal tabs and ssh into each of them. (Chris likes using pdo4)

Run on the PDO computers. As of Sector 42 TEC runs under python 3\. TEC will fail under python 2.7. You will need to set up a python 3 environment on pdo. I can probably help anyone with that, I just downloaded and installed the anaconda package. 

The following python modules should be available on PDO and are used by TEC numpy, matplotlib, scipy, astropy, astroquery, h5py, statsmodels, spectrum

The following system commands should be available on PDO c++ compiler, pdftotext, grep, gs, seq, parallel, wkhtmltopdf

One time you need to compile the modshift test c++ code. After downloading the TEC source code (see below) in the code directory  
g++ \-std=c++11 \-Wno-unused-result \-O3 \-o modshift \-O modshift.cpp  
In modshift\_test.py Line 498 the syscall variable needs to point to the compiled modshift.

In my .bashrc I have the following alias and function  
\#\#\# TEC  
alias sedcsvfix="sed \-e 's/\\"\\"//g' \-e 's/,\\"\[^\\"\]\*/,\\"NOCOMMENT/g'"  
function teccd { cd /pdo/users/cjburke/spocvet/sector"$1"/TESS-ExoClass/code; }  
export \-f teccd  
\#\#\# TEC items  
The alias is used to remove commas in the TEV output TOI listing .csv and the function is used to quickly change to the working code directory of a sector. For instance ‘teccd 33’ will change to where I ran TEC on sector 33\. Alter the path for where you are running TEC.

Text in this color is directions for a multi-sector run

# Directory and code setup

I run TEC under the /pdo/users/cjburke/spocvet, alter the path to your directory of choice

* cd /pdo/users/cjburke/spocvet   
* mkdir sector\#  
* cd sector\#  
* mkdir S\# (e.g., S75) (mkdir S-1; for multi-sector, yes, always “S-1” no matter what sectors are included)  
* mkdir pdfs  
* mkdir tevpdfs

Clone from github the TEC codebase

* git clone https://github.com/christopherburke/TESS-ExoClass.git  
* cd TESS-ExoClass/code   (copy a more recent version of ***twexo.py*** from Katharine or Glen working area)

This is the main working directory for all TEC commands.

Set the parameters for TEC using tec\_make\_params.py  
This routine also downloads the latest TOI catalog and that takes a while to do.   
Need to update the curl command on lineto point to new TEV TOI catalog, namely: "[https://tev.mit.edu/toi/toi-release/](https://tev.mit.edu/toi/toi-release/)"

* python3 tec\_make\_params.py \#  
  where \# is the sector number  
* python tec\_make\_params.py 14 60 \-spocdir sector-014-026+040-060

               (this is an example from the multisector 14 \- 60 run, the directory name is  
                actually “sector-014-026+040-060”)

If you are ever curious the parameters that TEC used for the run are kept in   
tec\_used\_params.py . This python script is created by tec\_make\_params.py, tec\_used\_params.py is what every routine reads to get its parameters.

Update tec\_datafile\_paths.dat  
   Add a line to this file to provide paths to the SPOC light curve files  
   one needs the prefix and suffix number of the light curve files. (prefix is from the ***sectorXX/light-curve*** directory, suffix is basically sequential, but both are also output from tec\_make\_params.py; namely, *LC File Prefix*, and *LC File Number*)

For TEC there are various times when commands are run in parallel and serially. Thus, I will open 6 ssh connections to pdo to have 6 terminals to run commands. I make use of teccd \<sector number\> bash alias to quickly go to the TEC working directory for each ssh connection.  
You should now be setup to run TEC commands

# TEC Commands

TEC commands are run from the TESS-ExoClass/code directory for the sector you are working on. The bashrc function ‘teccd \#’ will take you there quickly. Some commands are run serially and some are run in parallel. For each command I will try to summarize what it calculates, when you should wait for command to complete before moving to next command, and what it outputs. For the outputs I am giving an example from Sector 33, the filenames will be different for the sector you are working on. A helper routine ‘python tec\_status.py’ exists that shows that the datafiles it expects for a TEC run are complete. Use ‘python tec\_status.py’ to help diagnose if a command is working or completed as expected.  
***(Most of these scripts have /pdo/users/cjburke/spocvet hardwired into output folder name. These need to be updated to your username)***

1. Read in the DV xml files for the SPOC TCEs and store the TCE data in a convenient format. Prereq: None. Wait until finished. Output: sector33\_20200208\_tce.h5 (can check \# of TCEs is as expected by checking DAWG ticket)  
   * python3  gather\_tce\_fromdvxml.py  
2. Output the TCE data in a human friendly .txt file. Prereq: Step 1\. Wait until finished. Output: sector33\_20200208\_tce.txt  
   * python3 dump\_tce\_info.py  
3. Bin all light curve files from 2min to 10minute. Prereq: None. Continue to next step while this is running. Output: Under the S\# directories each light curve will be stored in .h5 format. Ex. for TIC 141122198 planet number 2 \~/spocvet/sector33/S33/141122/tess\_dvts\_0000000141122198\_02.h5d  
   * python3 dvts\_bulk\_resamp.py  
4. Find cadences where many transit ephemerides overlap such that the transits should be deweighted when recalculating significance. Prereq: Single sector none; Multisector wait until step 3 completes. Continue to next step while this is running. Output: Will bring up a figure window. Close figure window. skyline\_data\_sector33\_20200208.txt; For some reason displaying the figure hangs from pdo on my current python setup? you will need to display the figure manually from the command line. \`display \-geometry 720x480 skyline\_spoc.png\` to verify the result and adjust BADSIGMA value for the Multisector runs. Step 9 seems to require more than one red dot on the plot (more than one line in your skyline\_data…txt file).

		MS only BADSIGMA set higher than nominal 2.75; if multisector it uses 3.5 automatically; no need to hardcode unless displaying the results are not satisfactory

* python3 skyline\_spoc.py  
5. Match TCE ephemerides to the known planet ephemerides at the exoplanet archive. This routine takes a long time since it needs to query MAST as well. This step can be a bit finicky. Every once in a while the queries to MAST will just hang and/or it will error out. Usually just rerunning the command will result in it working. Prereq: Single sector None; Multisector wait until step 3 completes.Continue to next step while this is running. Output: federate\_knownP\_sector33\_20200208.txt

        **\*\*\*If TESS changes the ecliptic pointing then line 234 search**

            **and filter needs to be modified. Also needs to be set to N or S.**

   * python3 federate\_knownPWtce.py  
6. Match TCE ephemeride list to itself. This finds matches in common indicating systematics. Prereq: Single Sector None; Multisector wait until step 3 completes. Continue to next step while this runs. Output: selfMatch\_sector33\_20200208.txt  
   * python3 selfMatch\_spoc.py  
7. Rip the difference image pages from the DV report. When running this command can sometimes produce ‘GPL Ghostscript…’ warnings and error messages. Those are actually ok. You can run tec\_status to see that the DV report pages are actually being generated. Prereq: None. Takes a long time to run so continue to next step while this is running. Output: Difference images in their own pdf for each TCE \~/spocvet/sector33/S33/141122/tess\_diffImg\_0000000141122198\_02\_33.pdf

		Multisector needs multiple instances run (recommend 3\) 

* python3 get\_dv\_report\_page.py  
  * seq 0 2 | parallel \--delay 60 \--results get\_dv\_report\_page\_results python3 get\_dv\_report\_page.py \-w {} \-n 3  
8. Parse the target pixel files to bin them to 10minute cadence in order to perform centroid analysis. Prereq: **\*\*Step 3, light curves must be rebinned before doing this**. Takes a long time to run so continue to next step while this runs. Output: target pixel file data in h5 format for every TCE \~/spocvet/sector33/S33/141122/tess\_tpf\_0000000141122198\_33.h5d  
   * python3 tpf\_bulk\_resamp.py  
   * For Multisector there is a file  tec\_datafile\_paths.dat that maintains the lightcurve paths, filenames, and suffix numbers. One needs to update this file to include the highest sector involved in the multisector run. These values can be obtained from looking in single sector updatefilenames.sh script. Take values from the NEW8 and NEW9 variables. Then one needs to specify the sectors involved in the multisector run in the same way as one would specify pages to print of a document. For example for a multisector sector 14-26 and sector 40-50.

   	\*\*\*Note no need to adjust resamp because these go back to the original 2min TPFs.

   	\*\*\*The sectors can be gotten from the DRN. e.g. for sector-14-78 the used

                    sectors from the DRM are 14-26,40,41,43,45,47-60,71-78

   * python3 tpf\_bulk\_resamp.py \-s 14-26,40-50  
9. Calculate the main statistics that will be used for the triage cut. Prereq: Step 3 AND 4 complete. The will use multiple cores and processes. The example below uses 20 processes. There is nothing special about 20 processes you can use more or less, but you have to change both the last number in the command and the 2nd number in the command, and the 2nd number in the command is one less than the last number. For instance if you want to run 5 processes the command should be ‘seq 0 4…-n 5’. Go to step 10 and wait until this completes before doing step 11\. Output: SES light curve for every TCE \~/spocvet/sector33/S33/141122/tess\_sesmes\_0000000141122198\_02.h5d  
   Code seems to require *skyline\_data..txt* file to contain more than 1 bad point, so if you get “len(badtimes) \< 2” errors, rerun skyline\_spoc.py with a slightly lower BADSIGMA value to get more than 1 line in your skyline\_data…txt file.   
   * seq 0 19 | parallel \--results ses\_mes\_results python3 ses\_mes\_stats.py \-w {} \-n 20  
10. Match the TOI ephemerides to the TCEs. The TOI catalog is downloaded during update\_filenames.sh Prereq: Wait until Step 5 completes. Output: federate\_toiWtce\_sector33\_20200208.txt  
    * python3 federate\_toiWtce.py  
11. Run the triage filter. Prereq: Step 9\. Wait until this completes but it is quick. Output: spoc\_fluxtriage\_sector33\_20200208.txt

           Check that the fluxtriage.txt file is the same length as the tce.txt file produced from Step 2 (minus 75 rows of header info)

* python3 flux\_triage.py  
12. Perform a trapezoid model fit and run the modshift test for the DV median detrended light curve. Prereq: Step 11\. Continue with next step while this runs. Output: Modshift plot outputs for every triage passing TCE and trapezoid fit parameters. \~/spocvet/sector33/S33/140900/tess\_0000000140900726\_01\_med-modshift.pdf & \~/spocvet/sector33/S33/140900/tess\_trpzdfit\_0000000140900726\_01.txt  
    * Edit modshift\_test.py to make sure Line 519 and 541 syscall points to compiled modshift  
    * python3 modshift\_test.py 1  
13. Perform the sweet test. Prereq: Step 11\. Continue with next step while this runs. Output: spoc\_sweet\_sector33\_20200208.txt
    Now supports parallel execution with \-w/\-n flags.
    * Serial: python3 sweet\_test.py
    * Parallel (13 cores): seq 0 12 | parallel \--results sweet\_test\_results python3 sweet\_test.py \-w {} \-n 13
    * After parallel run, concatenate per-worker outputs: cat spoc\_sweet\_\*\_w\*.txt \> spoc\_sweet\_sector33\_20200208.txt
14. Gather the flux weighted centroid time series and some PDC statistics about the quality of the light curve. Prereq: Step 11\. Continue with next step while this runs. Output: \~/spocvet/sector33/S33/140900/tess\_flxwcent\_0000000140900726\_01.h5d
    Now supports parallel execution with \-w/\-n flags. No output merging needed (per-TCE HDF5 files).
    * For multisector needs the sector list on the command line see Step 8\.
    * Serial: python3 grab\_flxwcent.py
    * Parallel (13 cores, single sector): seq 0 12 | parallel \--results grab\_flxwcent\_results python3 grab\_flxwcent.py \-w {} \-n 13
    * Parallel (13 cores, multisector): seq 0 12 | parallel \--results grab\_flxwcent\_results python3 grab\_flxwcent.py \-s 14-26,40-50 \-w {} \-n 13
15. Check whether the TCE events line up with momentum dumps. Prereq: Step 11\. Continue with next step while this runs. Output: spoc\_modump\_sector33\_20200208.txt
    Now supports parallel execution with \-w/\-n flags.
    * Serial: python3 modump\_check.py
    * Parallel (13 cores): seq 0 12 | parallel \--results modump\_check\_results python3 modump\_check.py \-w {} \-n 13
    * After parallel run, concatenate per-worker outputs: cat spoc\_modump\_\*\_w\*.txt \> spoc\_modump\_sector33\_20200208.txt  
16. Generate the twexo page that has convenient URL links and GAIA data. UPDATE tess-point by manually copying new version into code directory if it needs to be updated. Prereq: Step 11\. Continue with next step while this runs. ***(Need to edit twexo.py/gen\_twexo.py to replace python with python3 in syscalls. Astroquery.gaia does not exist in python2.7). ALSO, need to edit twexo.py to change outputDir to not cjburke.*** (This step can take a couple of days)  
    * python3 gen\_twexo.py  
17. Run modshift test again, but using the TEC detrended light curve. Run this after getting the other steps 12-16 have started. Prereq: Step 11\. Now we wait for steps 12-17 to finish.  
    * python3 modshift\_test.py 2  
18. Generate TEC centroid difference image figures. So far this is not that useful other than egregious centroid offsets. This is a multi-core step. Prereq: Step 11,12, & 17\. If you run this step wait until it finishes until moving onto step 19\. Output: Difference image figures \~/spocvet/sector33/S33/140900/tess\_bsc\_diffImg\_0000000140900726\_01\_33.pdf  
    * seq 0 19 | parallel \--results centroid\_basic\_results python3 centroid\_form\_basic.py \-w {} \-n 20  
19. Make the TEC Tier files. This is where we bring all the information together for the final ranking. Prereq: Wait until all steps 1-17 (optionally 18 as well) are complete. Before running this step I run ‘python3 tec\_status.py’ to ensure that I have all the tests completed. Also, ‘ls \-l \*txt’ to make sure there aren’t any zero length files. This step is very quick. Output: spoc\_ranking\_Tier1\_sector33\_20200208.txt as well as Tier2 and Tier3 file.  
    * python3 rank\_tces.py  
20. Generate the TEC reports. Prereq: Step 19\. This uses multiple processes. Outputs: \~/spocvet/sector33/pdfs/  
    * seq 0 19 | parallel \--results rank\_tces\_results python3 rank\_tces.py \-w {} \-n 20  
    * After this is done I run ‘python3 tec\_status.py’ to make sure all the TEC reports are generated. Also, check to make sure there aren’t too small files; ‘ls \-Shlr \*pdf | head’. They should all be \> several MB in size  
      

21\.  Formally TEC is complete. There is another step that is not in the TEC codebase that does the merging of DV mini reports with the TEC report for the ingest to TEV. This code is at /pdo/users/cjburke/spocvet/merge4tev.py  
Make a copy of merge4tev.py into your working directory.  
Alter the variables (*mini* stuff based on files found in /pdo/spoc-data/sector-033/dv-reports/)  
    sourceDir \= '/pdo/users/cjburke/spocvet/sector33/pdfs'  
    outDir \= '/pdo/users/cjburke/spocvet/sector33/tevpdfs'  
    miniDir \= '/pdo/spoc-data/sector-033/dv-reports/'  
    miniHdr \= 'tess2020353052510-'  
    miniTail \= '-00430\_dvm.pdf'  
    multiSector \= False  
    SECTOR \= 33  
    multiSector \= True  
    SECTOR \= 78 (this only seemed to work when I used the LAST sector of the multi)  
To point to where various things live and then run it with multiple processes

* seq 0 19 | parallel \--results merge\_results python3 merge4tev.py \-w {} \-n 20

I run tec\_status.py again to make sure the TEV merged reports are generated.

**How to diagnose a problem step that uses the parallel command to launch routines**  
parallel creates a directory for every process launched to store the stdout and stderr.  The directory names that store the outputs match what is given after the ‘--results’ flag in the parallel command. For instance ‘--results ses\_mes\_results’ means look in the ses\_mes\_results directory for the outputs. There is one more level of directory as well with name ‘1’. So, in summary ‘cd ses\_mes\_results/1’ will get you to the directory containing a separate directory for every process. Each process directory is numbered. From the ‘ses\_mes\_results/1’ directory, run the command ‘tail \-n 100 \*/stdout | less’. This will list the last 100 lines of stdout for every process. A lot of times the error is actually in stdout. You can also try ‘tail \-n 100 \*/stderr | less’ if you don’t find anything useful in stdout.  
