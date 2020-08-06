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
parser.add_argument('--html', type=str,
                    help='directory to create and relocate fastqc reports to for easy viewing', default='n')
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


# STEP 1) Get a list of all libraries contained in the directory (args.d)
directoryContents = []
directoryContents += [each for each in os.listdir(args.d) if each.endswith('.gz') or each.endswith('.fastq')]
#print(directoryContents, end = " ");
#print(" is the list of libraries in the directory")

libFile_list = []
print("\nLIBRARY IDs IN THE CHOSEN DIRECTORY:\n", end = " ")
for libOutput in directoryContents:
    basename1 = libOutput.split("_")[0]
    libFile_list.append(basename1)
    #print("\t" + libOutput)
    print("\t" + basename1)
    

# STEP 2) Build the list of library IDs to include (default, if no list, select all)
#   (args.l)
libsToJoin = []
matchedList = []

if args.l == "all":
    print("\nNO LIST GIVEN. USING ALL LIBRARIES\n", end = " ")
    libFile_list_sorted = sorted(libFile_list)
    #print(libFile_list_sorted)
    #print("is the list of libraries we will use")
else:
    print("\nSELECTING THE FOLLOWING LIBRARIES:\n", end = " ")
    libList = open(args.l, "r")
    for i in libList:
        i = i.rstrip("\n")
        libsToJoin.append(i)
        #print("\t" + i)
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
    matchedListInOrder = sorted(matchedList)
    for i in matchedListInOrder:
        print("\t" + i)
    #print(" are the libraries to select")


# STEP 3) Scan through directory & unzip any zipped files
#  (based on provided list of library IDs, or all by default)
print("\n\t...NOW UNZIPPING FILES...\n")

unzipList = []
if args.l == 'all':
    for root, dirs, files in os.walk(args.d):
        for file in files:
            if file.endswith('fastqc.zip'):
                fileToUnzip = os.path.join(root, file)
                basename = file.split('_')[0]
                if basename in libFile_list_sorted:
                    unzipList.append(fileToUnzip)
                    #print(basename)
    #print(unzipList)
else:
    for root, dirs, files in os.walk(args.d):
        for file in files:
            if file.endswith('fastqc.zip'):
                fileToUnzip = os.path.join(root, file)
                basename = file.split('_')[0]
                if basename in matchedListInOrder:
                    unzipList.append(fileToUnzip)
                    #print(basename)
    #print(unzipList)
    
# Unzip files in the list
for i in unzipList:
    #print("UNZIPPING " + i + ' into the same directory ...')
    zipDirec = i.rsplit('/', 1)[0]
    #print(zipDirec)
    with ZipFile(i, 'r') as zip:
    #    print(root)
        zip.extractall(zipDirec)

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

with open('alignmentStats.tsv', 'a') as flatfile:
    flatfile.seek(0)
    flatfile.truncate()
    flatfile.write('SAMPLE')
    flatfile.write('\t')
    flatfile.write('reads_HS')
    flatfile.write('\t')
    flatfile.write('alignRate_genome')
    flatfile.write('\t')
    flatfile.write('SAMPLE')
    flatfile.write('\t')
    flatfile.write('reads_FC')
    flatfile.write('\t')
    flatfile.write('assignRate_annotation')
    flatfile.write('\n')
    flatfile.close 

print("\n\tDONE WRITING OUTFILE HEADERS\n")

# Make the output directory for .html files
if args.html == 'n':
    print("\tNo .html files will be moved...\n")
else:
    #os.mkdir('/Users/HVE/Desktop/fastqc_reports')
    #print(args.html)
    try:
        os.mkdir(args.html)
    except OSError:
        #print ("Creation of the directory %s failed" % newDirec)
        print(args.html + " already exists")
    else:
        print ("Successfully created the directory " + args.html)
    
# STEP 5) Write the summary file, copy all html files to a folder for easy viewing (if args.html provided)
if args.l == 'all':
    for root, dirs, files in os.walk(args.d):
        if root.endswith('fastqc'):
            #print(root)
            fileName = root.rsplit("/", 1)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in libFile_list_sorted:
                summaryPath = os.path.join(root, 'summary.txt')
                dataPath = os.path.join(root, 'fastqc_data.txt')
                url = os.path.join(root, 'fastqc_report.html')
                #print(summaryPath)
                if args.html == "n":
                    #print("not moving html files")
                    url2 = os.path.join(root, 'fastqc_report.html')
                else:
                    newFile = root.rsplit('/', 1)
                    #print(newFile)
                    #print(" is the file to create")
                    newDirec = os.path.join(args.html, newFile[1])
                    #print(newDirec + " is the directory to create")
                    dst = os.path.join(args.html, newFile[1], 'fastqc_report.html')
                    #print(dst + " is the destination")
                    #url2 = os.path.join(args.html, newFile[1], 'fastqc_report.html')
                    # UNCOMMENT IF USING RAVEN:
                    url2 = os.path.join('http://raven.anr.udel.edu/fastqc_reports', newFile[1], 'fastqc_report.html')
                    #print(url2 + " is url to write to file")
                    try:
                        os.mkdir(newDirec)
                    except OSError:
                        #print ("Creation of the directory failed" + newDirec)
                        print(newDirec + " already exists")
                    else:
                        print ("Successfully created the directory " + newDirec)
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
                            #summaryOutFile.write(totalSeq + "\n")
                            summaryOutFile.write(totalSeq)
                summaryOutFile.close()
else:
    for root, dirs, files in os.walk(args.d):
        if root.endswith('fastqc'):
            #print(root)
            fileName = root.rsplit("/", 1)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in matchedListInOrder:
                summaryPath = os.path.join(root, 'summary.txt')
                dataPath = os.path.join(root, 'fastqc_data.txt')
                url = os.path.join(root, 'fastqc_report.html')
                #print(summaryPath)
                if args.html == "n":
                    #print("not moving html files")
                    url2 = os.path.join(root, 'fastqc_report.html')
                else:
                    newFile = root.rsplit('/', 1)
                    #print(newFile)
                    #print(" is the file to create")
                    newDirec = os.path.join(args.html, newFile[1])
                    #print(newDirec + " is the directory to create")
                    dst = os.path.join(args.html, newFile[1], 'fastqc_report.html')
                    #print(dst + " is the destination")
                    #url2 = os.path.join(args.html, newFile[1], 'fastqc_report.html')
                    # UNCOMMENT IF USING RAVEN:
                    url2 = os.path.join('http://raven.anr.udel.edu/fastqc_reports', newFile[1], 'fastqc_report.html')
                    #print(url2 + " is url to write to file")
                    try:
                        os.mkdir(newDirec)
                    except OSError:
                        #print ("Creation of the directory failed" + newDirec)
                        print(newDirec + " already exists")
                    else:
                        print ("Successfully created the directory " + newDirec)
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
                            #summaryOutFile.write(totalSeq + "\n")
                            summaryOutFile.write(totalSeq)
                summaryOutFile.close()

print("\n\tDONE WRITING SUMMARY FILE\n")


# STEP 6) Write the OR sequences file, if desired
if args.OR == "y":
    if args.l == 'all':
        for root, dirs, files in os.walk(args.d):
            if root.endswith('fastqc'):
                #print(root)
                fileName = root.rsplit("/", 1)[1]
                #print(fileName)
                basename = fileName.split("_")[0]
                #print(basename)
                if basename in libFile_list_sorted:
                    dataPath = os.path.join(root, 'fastqc_data.txt')
                    #print(".")
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
    else:
        for root, dirs, files in os.walk(args.d):
            if root.endswith('fastqc'):
                #print(root)
                fileName = root.rsplit("/", 1)[1]
                #print(fileName)
                basename = fileName.split("_")[0]
                #print(basename)
                if basename in matchedListInOrder:
                    dataPath = os.path.join(root, 'fastqc_data.txt')
                    #print(".")
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

# STEP 7) Get mapping statistics from hisat2 and featurecounts                               




# Store the libraries we want in a list
alignFileList = []
#assignFileList = []
if args.l == 'all':
    for root, dirs, files in os.walk(args.d):
        if root.endswith('hisat_out'):
            fileName = root.rsplit("/", 2)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in libFile_list_sorted:
                alignFilePath = os.path.join(root, 'align_summary.txt')
                #print(alignFilePath + " is the alignment File we want")
                alignFileList.append(alignFilePath)
                #print(".")
                #print(dataPath + " IS THE DATA FILE PATH")
        if root.endswith('rawcounts_output'):
            fileName = root.rsplit("/", 2)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in libFile_list_sorted:
                assignFilePath = os.path.join(root, 'countRunsummary.txt')
                #print(alignFilePath + " is the alignment File we want")
                alignFileList.append(assignFilePath)
                #print(".")
                #print(dataPath + " IS THE DATA FILE PATH")
else:
    for root, dirs, files in os.walk(args.d):
        if root.endswith('hisat_out'):
            fileName = root.rsplit("/", 2)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in matchedListInOrder:
                alignFilePath = os.path.join(root, 'align_summary.txt')
                #print(alignFilePath + " is the alignment File we want")
                alignFileList.append(alignFilePath)
                #print(".")
                #print(dataPath + " IS THE DATA FILE PATH")
        if root.endswith('rawcounts_output'):
            fileName = root.rsplit("/", 2)[1]
            #print(fileName)
            basename = fileName.split("_")[0]
            #print(basename)
            if basename in matchedListInOrder:
                assignFilePath = os.path.join(root, 'countRunsummary.txt')
                #print(alignFilePath + " is the alignment File we want")
                alignFileList.append(assignFilePath)
                #print(".")
                #print(dataPath + " IS THE DATA FILE PATH")
alignFiles_sorted = sorted(alignFileList)
#print(alignFiles_sorted)


with open('alignmentStats.tsv', 'a') as outFile:
    for i in alignFiles_sorted:
        with open(i) as inFile:
                #print(i)
            fileName = i.rsplit("/", 3)[1]
            basename = fileName.split("_")[0]
            for i, line in enumerate(inFile):
                if re.search("reads", line):
                    reads = line.split(" ")[0]
                if re.search("overall", line):
                    alignPercent = line.split(" ")[0]
                    #print(basename + '\t' + reads + '\t' + alignPercent + '\t', end = ' ')
                    outFile.write(basename + '\t' + reads + '\t' + alignPercent + '\t')
                    #alignRate = basename + '\t' + reads + '\t' + alignPercent + '\t'
                    #print(alignRate)
                    #outFile.write(alignRate)
                if re.search("Total", line):
                    total = (line.split(" ")[7])
                if re.search("Successfully", line):
                    percent=(line.split(" ")[9])
                    #assignRate = (basename + '\t' + total + '\t' + percent + '\n')
                    #print(basename + '\t' + total + '\t' + percent + '\n')
                    outFile.write(basename + '\t' + total + '\t' + percent + '\n')

print("\n\tDONE WRITING ALIGNMENT STATS FILE\n")
                
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



if args.l == "all":
    print("\n")
else:
    matchedListInOrder = sorted(matchedList)
    print("\nMATCHING LIBRARIES:\n", end = " ")
    for i in matchedListInOrder:
        print("\t" + i)

        #zip.extractall(os.path.join(root))

        #if root.endswith('/qc'):
        #    print(root)
            #basename = root.rsplit('/', 2)[1]
            #libNum = basename.split('_')[0]
            #print(libNum)
            #if libNum in matchedListInOrder:
                #print(libNum + " is in the list")
            #    alignFilePath = os.path.join(root, 'alignSummary.txt')
            #    print(alignFilePath + " is the alignment File we want")
            #    alignFileList.append(alignFilePath)
    #print("Using the following libraries:\n")
    #print(libFile_list)
    

exit()
if args.l == 'all':
    print()
else:
    print("Using the following libraries:\n")
    print(matchedListInOrder)
    for root, dirs, files in os.walk(args.d):
        if root.endswith('/qc'):
            print(root)
            #basename = root.rsplit('/', 2)[1]
            #libNum = basename.split('_')[0]
            #print(libNum)
            #if libNum in matchedListInOrder:
                #print(libNum + " is in the list")
            #    alignFilePath = os.path.join(root, 'alignSummary.txt')
            #    print(alignFilePath + " is the alignment File we want")
            #    alignFileList.append(alignFilePath)
    print(unzipList)

exit()

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
                            
for i in files:
    if root.endswith('fastqc'):     
        #print(root)
        #print(files)
        #print(".")
        #print(root + " MIGHT BE A ROOT WE WANT")
        #summaryPath = os.path.join(root, 'summary.txt')
        #print(summaryPath + " IS THE SUMMARY FILE PATH")
        #dataPath = os.path.join(root, 'fastqc_data.txt')
        #url = os.path.join(root, 'fastqc_report.html')
        newFile = root.rsplit('/', 1)
        newDirec = os.path.join('/var/www/html/fastqc_reports', newFile[1])
        dst = os.path.join('/var/www/html/fastqc_reports', newFile[1], 'fastqc_report.html')
        url2 = os.path.join('http://raven.anr.udel.edu/fastqc_reports', newFile[1], 'fastqc_report.html')
        #dst = os.path.join('/Users/HVE/Desktop/fastqc_reports', newFile[1], 'fastqc_report.html')
        #try:
        #    os.mkdir(newDirec)
        #except OSError:
        #    print ("Creation of the directory %s failed" % newDirec)
        #else:
        #    print ("Successfully created the directory %s " % newDirec)
        #copyfile(url, dst)
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
        
alignFileList = []
if args.l == 'all':
    print("Using the following libraries:\n")
    print(libFile_list)
else:
    print("Using the following libraries:\n")
    print(matchedListInOrder)
    for root, dirs, files in os.walk(args.d):
        if root.endswith('/hisat_out'):
            basename = root.rsplit('/', 2)[1]
            libNum = basename.split('_')[0]
            #print(libNum)
            if libNum in matchedListInOrder:
                #print(libNum + " is in the list")
                alignFilePath = os.path.join(root, 'alignSummary.txt')
                print(alignFilePath + " is the alignment File we want")
                alignFileList.append(alignFilePath)
print(alignFileList)

for i in infile:
    for j in assignFileList:
        with open(j) as inFile2:
            #print(j)
            fileName = j.rsplit("/", 3)[1]
            basename = fileName.split("_")[0]
            #print(fileName)
            #print(basename)
            for j, line in enumerate(inFile2):
                if re.search("Total", line):
                    total = (line.split(" ")[7])
                if re.search("Successfully", line):
                    percent=(line.split(" ")[9])
                    assignRate = (basename + '\t' + total + '\t' + percent + '\n')
                    #print(assignRate)
                    outFile.write(alignRate + "\t" + assignRate)
    

