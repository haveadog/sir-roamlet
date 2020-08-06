#!/usr/bin/python3

# Purpose: to scan through the FRANKENSEQ LITE output directory
# and parse the mapping alignment statistics into one excel-readable file


# Steps:
#     1) Iterate through directory of frankenseq output with the following structure:
#         
#     theDirectoryRNAOutput
#         DX_9999_S_.....fq.gz
#             hisat_out
#                 align_summary.txt
#             stringtie_out
#             rawcounts_output
#                 _______fcounts.summary
#
#     2) align_summary.txt - line 14 (total mapping percent)
#     3) fcounts summary - get percentage mapped (divide assigned reads by sum of total reads)
#     4) print filename (with lib ID), mapping alignment, and featurecounts percentages in an excel readable table


import os
import sys
import re

# DECLARE VARIABLES

direc_to_scan = "/var/www/subdirectories_for_interface/theDirectoryRNAOutput/spr17_D6D16redo"

allStats = os.path.join(direc_to_scan, "D6D16redo_alignment.txt")                       # the name of the file to output
fcountStats = os.path.join(direc_to_scan, "D6D16redo_fcountStats.txt")
      

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
