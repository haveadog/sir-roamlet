#!/usr/bin/python3

### ........ ABOUT ........###

# v_2020.6.17
# Written by Heidi A. Van Every

# PURPOSE: Iterate through directory of sequencing library output and
#   write a script to join desired count or expression files for downstream analysis.
#   Additionally, create two tab-separated files with ordered headers for use in R and JMP

# FUTURE: make sure files are in same order and have same number of lines, columns, order etc before writing join script
#   Useful script to check that number of columns is the same in every row:
#       awk '{print NF}' <file> | uniq -c
#   After running join script, append the file with the header list
#   Flag duplicate lib #s
#   Execute the script after writing it

# To generate join script:
#   python joinScriptWriter.py > joinScript.sh
# Once you are satisfied, run the join script:
#   bash joinScript.sh

# Example script:
# join countFile1.tsv countFile2.tsv | join - countFile3.tsv | [...] join - countFileN.tsv > joinedCounts.tsv

# join_exprs_table.py -h

#usage: livJoin.py [-h] libDirectory libList dataType outFile

#Iterate through directory of library output folders. Write a script to join
#them into an expression table.

#positional arguments:
#  libDirectory  the path to the library output directories
#  libList       .txt file containing a list of library IDs to select
#  dataType      the type of data to join (options: tpm, fpkm, or counts)
#  outFile       name of output file

#optional arguments:
#  -h, --help    show this help message and exit


### ........ IMPORT MODULES ........###

import glob
import os
import sys
import argparse
import re


### ........ DEFINE COMMAND LINE ARGUMENTS & VARIABLES ........###

parser = argparse.ArgumentParser(description='Iterate through directory of library output folders. Write a script to join them into an expression table.')
#parser.add_argument('libDirectory', metavar='-d', type=str, help='the path to the library output directories')
parser.add_argument('libDirectory', type=str,
                    help='the path to the library output directories')

parser.add_argument('libList', type=str,
                    help='.txt file containing a list of library IDs to select')

parser.add_argument('dataType', metavar='dataType', type=str, choices = ("tpm", "fpkm", "counts", "all"),
                    help='the type of data to join (options: tpm, fpkm, or counts)')

parser.add_argument('outFile', type=str,
                    help='base name of output file (s)')

args = parser.parse_args()
#print(args.libDirectory)
#print(args.libList)
#print(args.dataType)
#print(args.outFile)


### ........ CODE ........###

# STEP 1) List the libraries contained in the directory
#   (argument = libDirectory)
directoryContents = []
directoryContents += [each for each in os.listdir(args.libDirectory) if each.endswith('.gz') or each.endswith('.fastq')]
#print(directoryContents, end = " ");
#print(" is the list of libraries in the directory")

libFile_list = []
print("\nLIBRARY IDs IN THE CHOSEN DIRECTORY:\n", end = " ")
for libOutput in directoryContents:
    basename1 = libOutput.split("_")[0]
    libFile_list.append(basename1)
    print("\t" + libOutput)

# STEP 2) List the libraries we want to join
#   (argument = libList)
libsToJoin = []
print("\nLIBRARIES TO JOIN:\n", end = " ")
libList = open(args.libList, "r")
for i in libList:
    i = i.rstrip("\n")
    libsToJoin.append(i)
    print("\t" + i)
libList.close()
#print(libsToJoin, end = " ");
#print(" are the libraries we want to join")

# STEP 3) Determine which library numbers match & sort in numerical order
matchedList = []
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
        #print("\t Writing join script without " + i + "...")
#print(matchedList, end = " ")
#print(" are the library IDs that match both lists")

matchedListInOrder = sorted(matchedList)
print("\nMATCHING LIBRARIES, IN THE ORDER TO JOIN:\n", end = " ")
for i in matchedListInOrder:
    print("\t" + i)
#print(matchedListInOrder, end = " ")
#print("are the library IDs that match both lists, in the order they will be joined")

# STEP 4) Write the join script
#   (argument = dataType)
#   Write to a bash file or execute directly
#with open("joinScript_tpm.sh", "w") as joinFile_tpm, open("joinScript_fpkm.sh", "w") as joinFile_fpkm, open("joinScript_counts.sh", "w") as joinFile_counts:

if args.dataType == "tpm":
   with open("joinScript_tpm.sh", "w") as joinFile_tpm:
      joinFile_tpm.write("join " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*TPM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*TPM.tsv")
      print("\nYOUR JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*TPM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*TPM.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_tpm.write(" | join - " + args.libDirectory + i + "*/stringtie_out/*TPM.tsv")
         print (" | join - " + args.libDirectory + i + "*/stringtie_out/*TPM.tsv", end =" ")
      joinFile_tpm.write(" > " + args.outFile + "_TPM.tsv")
      print(" > " + args.outFile + "_TPM.tsv")
      print("When you are satisfied, run the following command:\n bash joinScript_tpm.sh")
elif args.dataType == "fpkm":
   with open("joinScript_fpkm.sh", "w") as joinFile_fpkm:
      joinFile_fpkm.write("join " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*FPKM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*FPKM.tsv")
      print("\nYOUR JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*FPKM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*FPKM.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_fpkm.write(" | join - " + args.libDirectory +  i + "*/stringtie_out/*FPKM.tsv")
         print(" | join - " + args.libDirectory + i + "*/stringtie_out/*FPKM.tsv", end =" ")
      joinFile_fpkm.write(" > " + args.outFile + "_FPKM.tsv")
      print(" > " + args.outFile + "_FPKM.tsv")
      print("When you are satisfied, run the following command:\n bash joinScript_fpkm.sh")
elif args.dataType == "counts":
   with open("joinScript_counts.sh", "w") as joinFile_counts:
      joinFile_counts.write("join " + args.libDirectory + (matchedListInOrder)[0] + "*/rawcounts_output/*RAWCOUNTS.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/rawcounts_output/*RAWCOUNTS.tsv")
      print("\nYOUR JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/rawcounts_output/*RAWCOUNTS.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/rawcounts_output/*RAWCOUNTS.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_counts.write(" | join - " + args.libDirectory + i + "*/rawcounts_output/*RAWCOUNTS.tsv")
         print(" | join - " + args.libDirectory + i + "*/rawcounts_output/*RAWCOUNTS.tsv", end =" ")
      joinFile_counts.write(" > " + args.outFile + "_RAWCOUNTS.tsv")
      print(" > " + args.outFile + "_RAWCOUNTS.tsv")
      print("When you are satisfied, run the following command:\n bash joinScript_counts.sh")
elif args.dataType == "all":
   with open("joinScript_all.sh", "w") as joinFile_all:
      joinFile_all.write("join " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*TPM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*TPM.tsv")
      print("\nYOUR TPM JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*TPM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*TPM.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_all.write(" | join - " + args.libDirectory + i + "*/stringtie_out/*TPM.tsv")
         print(" | join - " + args.libDirectory + i + "*/stringtie_out/*TPM.tsv", end =" ")
      joinFile_all.write(" > " + args.outFile + "_TPM.tsv")
      print(" > " + args.outFile + "_TPM.tsv")
      joinFile_all.write("\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*FPKM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*FPKM.tsv")
      print("\nYOUR FPKM JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/stringtie_out/*FPKM.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/stringtie_out/*FPKM.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_all.write(" | join - " + args.libDirectory + i + "*/stringtie_out/*FPKM.tsv")
         print(" | join - " + args.libDirectory + i + "*/stringtie_out/*FPKM.tsv", end =" ")
      joinFile_all.write(" > " + args.outFile + "_FPKM.tsv")
      print(" > " + args.outFile + "_FPKM.tsv")
      joinFile_all.write("\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/rawcounts_output/*RAWCOUNTS.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/rawcounts_output/*RAWCOUNTS.tsv")
      print("\nYOUR COUNTS JOIN COMMAND IS:\njoin " + args.libDirectory + (matchedListInOrder)[0] + "*/rawcounts_output/*RAWCOUNTS.tsv " + args.libDirectory + (matchedListInOrder[1]) + "*/rawcounts_output/*RAWCOUNTS.tsv", end =" ")
      for i in (matchedListInOrder)[2:]:
         joinFile_all.write(" | join - " + args.libDirectory + i + "*/rawcounts_output/*RAWCOUNTS.tsv")
         print(" | join - " + args.libDirectory + i + "*/rawcounts_output/*RAWCOUNTS.tsv", end =" ")
      joinFile_all.write(" > " + args.outFile + "_RAWCOUNTS.tsv")
      print(" > " + args.outFile + "_RAWCOUNTS.tsv")
      print("When you are satisfied, run the following command:\n bash joinScript_all.sh")

#with open("joinScript.sh", "a") as joinFile:
#    joinFile.write("> " + args.outFile)
#print("> " + args.outFile)

# STEP 5) Write the header files
with open("R_header.txt", 'w') as headerFile:
   for i in matchedListInOrder:
    headerFile.write("\"" + i + "\", ")
with open("JMP_header.txt", 'w') as headerFile2:
   for i in matchedListInOrder:
    headerFile2.write(i + "\t")



