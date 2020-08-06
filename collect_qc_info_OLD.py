#!/usr/bin/python3

### ........ ABOUT ........###

# v_2020.6.19
# Written by Heidi A. Van Every

# Parse FastQC output and summarize,
# and/or collect overrepresented sequences for use with blast.
# NOTE: Currently will not distinguish between previously unzipped fastqc files,
# and those you specifically wish to include (if specifying a list of library IDs)
# FUTURE: Fix this problem ^^
# - Allow specification of trimmed or untrimmed fastq files
# - Copy .html files to location they can be viewed on server (/var/www/html/fastqc_reports)
# - Parse OR sequences file to get total percentages and automatically submit to blast

### ........ IMPORT MODULES ........###

import os
import sys
import re
import argparse
from zipfile import ZipFile
from shutil import copyfile

### ........ DEFINE COMMAND LINE ARGUMENTS & VARIABLES ........###

cwd = os.getcwd()

parser = argparse.ArgumentParser(description='Parse FastQC output and summarize, and/or collect overrepresented sequences for use with blast.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--d', type=str, default=cwd,
                    help='The path to the library output directories')
parser.add_argument('--l', type=str,
                    help='.txt file containing a list of library IDs to select', default='all')
parser.add_argument('--OR', type=str, choices = ("y", "n"), default='n',
                    help='Indicate if you would like to collect overrepresented sequences? (y = yes, n = no')
#parser.add_argument('--fq', metavar = '-fq', type=str, choices = ("t", "u", "a"), default='a',
#                    help='Collect data from trimmed, untrimmed, or all (options: t = trimmed, u = untrimmed, a = all)')

args = parser.parse_args()

# Reiterate options:
print("\nOPTIONS:")
print("\tROOT DIRECTORY: " + args.d)

if args.l == "all":
    print("\tLIBRARY LIST: None provided, we will use all library IDs in the directory") 
else:
    print("\tLIBRARY LIST: " + args.l)
    
if args.OR == "n":
    print("\tCOLLECTING OR SEQUENCES: No") 
elif args.OR == "y":
    print("\tCOLLECTING OVERREPRESENTED SEQUENCES: Yes")
    
#if args.fq == "t":
#    print("\tFASTQ TYPE: Only collecting data from TRIMMED fastq files") 
#elif args.fq == "u":
#    print("\tFASTQ TYPE: Only collecting data from UNTRIMMED fastq files")
#elif args.fq == "a":
#    print("\tFASTQ TYPE: None selected, collecting data from both TRIMMED and UNTRIMMED fastq files")


# STEP 1) List the libraries contained in the directory
#   (args.d)
directoryContents = []
directoryContents += [each for each in os.listdir(args.d) if each.endswith('.gz') or each.endswith('.fastq')]
#print(directoryContents, end = " ");
#print(" is the list of libraries in the directory")

libFile_list = []
print("\nLIBRARY IDs IN THE CHOSEN DIRECTORY:\n", end = " ")
for libOutput in directoryContents:
    basename1 = libOutput.split("_")[0]
    libFile_list.append(basename1)
    print("\t" + libOutput)


# STEP 2) List the libraries we want to include (default, if no list, select all)
#   (args.l)
libsToJoin = []
matchedList = []

if args.l == "all":
    print("\nUSING ALL LIBRARIES...\n", end = " ")
else:
    print("\nLIBRARIES TO SELECT:\n", end = " ")
    libList = open('libsToJoin.txt', "r")
    for i in libList:
        i = i.rstrip("\n")
        libsToJoin.append(i)
        print("\t" + i)
    libList.close()
    for i in libsToJoin:
        if i in libFile_list:
            #print(i);
            #print(" matches both lists")
            matchedList.append(i)
        elif i not in libFile_list:
            answer = str(input("\nERROR: " + i + " is not in the directory. Would you like to continue anyway? (y/n)"))
            if answer == "y":
                print("\n\tOk, continuing...")
            elif answer == "n":
                print("\n\tOk, go find your missing file...")
                exit()
            else:
                print("\n\tInvalid_answer. Please enter y (yes) or n (n).")
                exit()
#print(matchedList)
matchedListInOrder = sorted(matchedList)

if args.l == "all":
    print("\n")
else:
    matchedListInOrder = sorted(matchedList)
    print("\nMATCHING LIBRARIES:\n", end = " ")
    for i in matchedListInOrder:
        print("\t" + i)
#print(matchedListInOrder, end = " ")
#print("are the library IDs that match both lists, in the order they will be joined")


# STEP 3) Scan through directory & unzip any zipped files
#  (based on provided list of library IDs, or all by default)
print("\n\tNOW UNZIPPING FILES...\n")

if args.l == 'all':
    for root, dirs, files in os.walk(args.d):
        if root.endswith('/qc'):
            #print(root + " IS THE QC DIRECTORY")
            for file in files:
                if file.endswith('fastqc.zip'):
                    #print(i + " is the lib ID we want")
                    #print(file + " is the file we found")
                    print("UNZIPPING " + file + ' into the same directory ...')
                    filePath = os.path.join(root, file)
                    #print(filePath + " is the file path")
                    with ZipFile(filePath, 'r') as zip:
                        zip.extractall(os.path.join(root))
else:
    for root, dirs, files in os.walk(args.d):
        if root.endswith('/qc'):
            #print(root + " IS THE QC DIRECTORY")
            for file in files:
                #filePath = os.path.join(root, file)
                #print(filePath)
                for i in matchedListInOrder:
                    if file.startswith(i) and file.endswith('fastqc.zip'):
                        #print(i + " is the lib ID we want")
                        #print(file + " is the file we found")
                        print("UNZIPPING " + file + ' into the same directory ...')
                        filePath = os.path.join(root, file)
                        #print(filePath + " is the file path")
                        with ZipFile(filePath, 'r') as zip:
                            zip.extractall(os.path.join(root))

print("\n\tDONE UNZIPPING FILES\n")


# STEP 4) Write the headers for the output files
with open('fastQC_summary.tsv', 'a') as flatfile:
    flatfile.seek(0)
    flatfile.truncate()
    flatfile.write('SAMPLE')
    flatfile.write('\t')
    flatfile.write('BasicStats')
    flatfile.write('\t')
    flatfile.write('PerBaseSeqQual')
    flatfile.write('\t')
    flatfile.write('PerTileSeqQual')
    flatfile.write('\t')
    flatfile.write('PerSeqQualScore')
    flatfile.write('\t')
    flatfile.write('PerBaseSeqContent')
    flatfile.write('\t')
    flatfile.write('PerSeqGC')
    flatfile.write('\t')
    flatfile.write('PerBaseN')
    flatfile.write('\t')
    flatfile.write('SeqLengthDist')
    flatfile.write('\t')
    flatfile.write('SeqDupLevels')
    flatfile.write('\t')
    flatfile.write('OverrepSeq')
    flatfile.write('\t')
    flatfile.write('AdapterCont')
    flatfile.write('\t')
    flatfile.write('URL')
    flatfile.write('\t')
    flatfile.write('Total#Seq')
    flatfile.write('\n')
    flatfile.close

if args.OR == "y":    
    with open('OR_Sequences.tsv', 'a') as flatfile:
        flatfile.seek(0)
        flatfile.truncate()
        flatfile.write('SAMPLE')
        flatfile.write('\t')
        flatfile.write('Sequence')
        flatfile.write('\t')
        flatfile.write('Count')
        flatfile.write('\t')
        flatfile.write('Percentage')
        flatfile.write('\t')
        flatfile.write('Possible_source')
        flatfile.write('\n')
        flatfile.close 

#print("\n\tDONE WRITING OUTFILE HEADERS\n")

#os.mkdir('/Users/HVE/Desktop/fastqc_reports')

# STEP 5) Write the summary file
# Also, copy all html files to a folder where they can be viewed
for root, dirs, files in os.walk(args.d):
    if root.endswith('fastqc'):     
        #print(files)
        #print(".")
        #print(root + " MIGHT BE A ROOT WE WANT")
        summaryPath = os.path.join(root, 'summary.txt')
        #print(summaryPath + " IS THE SUMMARY FILE PATH")
        dataPath = os.path.join(root, 'fastqc_data.txt')
        url = os.path.join(root, 'fastqc_report.html')
        newFile = root.rsplit('/', 1)
        newDirec = os.path.join('/var/www/html/fastqc_reports', newFile[1])
        dst = os.path.join('/var/www/html/fastqc_reports', newFile[1], 'fastqc_report.html')
        url2 = os.path.join('http://raven.anr.udel.edu/fastqc_reports', newFile[1], 'fastqc_report.html')
        #dst = os.path.join('/Users/HVE/Desktop/fastqc_reports', newFile[1], 'fastqc_report.html')
        try:
            os.mkdir(newDirec)
        except OSError:
            print ("Creation of the directory %s failed" % newDirec)
        else:
            print ("Successfully created the directory %s " % newDirec)
        copyfile(url, dst)
        with open(str(summaryPath), 'r') as summaryFile, open(str(dataPath), 'r') as dataFile, open('fastQC_summary.tsv', 'a') as summaryOutFile:
            #summaryOutFile.write("sample\t")
            for i, line in enumerate(summaryFile):
                if i ==0:
                    #print(line)
                    filename = line.split('\t')[2]
                    #print(filename)
                    libNum = filename.split('_')[0]
                    if re.match('^\d{3,4}_S.{1,14}_val_1', filename):
                        sample = (libNum + "_R1_trimmed")
                    if re.match('^\d{3,4}_S.{1,14}_val_2', filename):
                            sample = (libNum + "_R2_trimmed")
                    if re.match('^\d{3,4}_S.{1,7}_R1_001.f', filename):
                        sample = (libNum + "_R1_untrimmed")
                    if re.match('^\d{3,4}_S.{1,7}_R2_001.f', filename):
                        sample = (libNum + "_R2_untrimmed")
                    summaryOutFile.write(sample +" \t")
                result = line.split('\t')[0]
                summaryOutFile.write(result + "\t")
            summaryOutFile.write(url2 + "\t")
            for i, line in enumerate(dataFile):
                if i ==6:
                    #print(line)
                    totalSeq = line.split('\t')[1]
                    #print(totalSeq)
                    summaryOutFile.write(totalSeq + "\n")
        summaryOutFile.close()
        
print("\n\tDONE WRITING SUMMARY FILE\n")


# STEP 6) Write the OR sequences file, if desired
if args.OR == "y":
    for root, dirs, files in os.walk(args.d):
        if root.endswith('fastqc'):
            #print(files)
            #continue
            #print(root + " IS THE ROOT WE WANT")
            print(".")
            #summaryPath = os.path.join(root, 'summary.txt')
            #print(summaryPath + " IS THE SUMMARY FILE PATH")
            dataPath = os.path.join(root, 'fastqc_data.txt')
            #print(dataPath + " IS THE DATA FILE PATH")
            with open(str(dataPath), 'r') as dataFile, open('OR_Sequences.tsv', 'a') as dataOutFile:
                #dataOutFile.write("sample\t")
                for i, line in enumerate(dataFile):
                    if i ==3:
                        #print(line)
                        filename = line.split('\t')[1]
                        print("Getting OR sequences in " + filename)
                        libNum = filename.split('_')[0]
                        if re.match('^\d{3,4}_S.{1,14}_val_1', filename):
                            sample = (libNum + "_R1_trimmed")
                        if re.match('^\d{3,4}_S.{1,7}_R1_001.f', filename):
                            sample = (libNum + "_R1_untrimmed")
                        if re.match('^\d{3,4}_S.{1,14}_val_2', filename):
                            sample = (libNum + "_R2_trimmed")
                        if re.match('^\d{3,4}_S.{1,7}_R2_001.f', filename):
                            sample = (libNum + "_R2_untrimmed")
                        #dataOutFile.write(sample +" \t")
                        inRecordingMode = False
                        for line in dataFile:
                            if not inRecordingMode:
                                if line.startswith('#Sequence'):
                                    inRecordingMode = True
                            elif line.startswith('>>END_MODULE'):
                                inRecordingMode = False
                                #return line
                            else:
                                #print(sample, line)
                                dataOutFile.write(sample + "\t" + line)
                    #result = line.split('\t')[0]
            dataOutFile.close()       
    print("\n\tDONE WRITING OR SEQUENCE FILE \n")
    
#with open ('OR_Sequences.tsv', 'r') as ORfile:
#    ORfile.groupby


# STEP 7) Get mapping statistics from hisat2 and featurecounts                               

with open('alignmentStats.tsv', 'a') as flatfile:
    flatfile.seek(0)
    flatfile.truncate()
    flatfile.write('SAMPLE')
    flatfile.write('\t')
    flatfile.write('reads_HS')
    flatfile.write('\t')
    flatfile.write('alignRate_genome')
    flatfile.write('\t')
    flatfile.write('reads_FC')
    flatfile.write('\t')
    flatfile.write('assignRate_annotation')
    flatfile.write('\n')
    flatfile.close 

if args.l == 'all':
    for root, dirs, files in os.walk(args.d):
        for file in files:
            if re.search("align_summary.txt", file):
                infile3 = os.path.join(root, file)


#allStats = os.path.join(direc_to_scan, "D6D16redo_alignment.txt")                       # the name of the file to output
#fcountStats = os.path.join(direc_to_scan, "D6D16redo_fcountStats.txt")
      
exit()

for root, dirs, files in os.walk(direc_to_scan):
    seqName = (dirs)
    for file in files:
        if re.search("align_summary.txt", file):
            infile3 = os.path.join(root, file)
            basename1 = infile3.split("/")[6]
            with open(infile3) as test:
                for i, line in enumerate(test):
                    if re.search("reads", line):
                        reads = line.split(" ")[0]
                    if re.search("overall", line):
                        alignPercent = line.split(" ")[0]
                        alignRate = basename1 + '\t' + reads + '\t' + alignPercent + '\n'
                        with open(allStats, 'a') as outFile:
                            outFile.write(alignRate)
for root, dirs, files in os.walk(direc_to_scan):
    seqName = (dirs)
    for file in files:
        if re.search("countRunsummary.txt", file):
            infile2 = os.path.join(root, file)
            basename = infile2.split("/")[6]
            with open(infile2) as test:
                for i, line in enumerate(test):
                    if re.search("Total", line):
                        total = (line.split(" ")[7])
                    if re.search("Successfully", line):
                        percent=(line.split(" ")[9])
                        assignRate = (basename + '\t' + total + '\t' + percent + '\n')
                        with open(fcountStats, 'a') as outFile2:
                            outFile2.write(assignRate)





exit()

          
    

