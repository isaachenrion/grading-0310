import os, csv
import argparse
from collections import OrderedDict
import numpy as np
import zipfile
import shutil
'''
This script is for merging the homework directories provided by the graders. They
will send you a bunch of zip files, which you decompress and provide as arguments
to --graders.

You will also need a blank copy of the grade directory. To get this,
go on NYU Classes, click "grade" under the appropriate assignment and then "download
all" in the top right. Check the boxes to get the grades as .csv and the feedback
comments.txt files. Make sure to get all students, even those who did not submit
(there is a check box for that). Unzip this file, and use it as the argument to
--source. You can use the same source for all homeworks, since it is just a
set of empty files and directories for each student.

The merged grades will go to --target, which you zip and upload to NYU
Classes.
'''

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=str, help='Source hw directory to get headers and directory names from.')
parser.add_argument('--hw_dir', type=str, help = 'homework directory')
parser.add_argument('--target', type=str, default='MASTER_GRADES', help='Target hw directory')
parser.add_argument('--graders', nargs='*', type=str, default=None, help='Grader directories')
args = parser.parse_args()

source = args.source
hw_dir = args.hw_dir
target = args.target
graders = args.graders

def main(commenting, grading, source, target, hw_dir=None, graders=None):
    students = next(os.walk(source))[1]
    for s in students: print(s)

    if graders is None:
        zipping = True
    if hw_dir is None:
        hw_dir = 'HW'

    if zipping:
        graders = []
        for file in os.listdir(hw_dir):
            if file.endswith(".zip"):
                graders.append(file.rstrip('.zip'))

        # unzip
        for grader in graders:
            grader_path = os.path.join(hw_dir, grader)
            zip_ref = zipfile.ZipFile(grader_path + '.zip', 'r')
            zip_ref.extractall(grader_path + '___temp')
            subdirs = os.listdir(grader_path+ '___temp')
            subdirs = [s for s in subdirs if s != '__MACOSX']; assert len(subdirs) == 1
            shutil.move(os.path.join(grader_path+ '___temp', subdirs[0]), grader_path)
            shutil.rmtree(os.path.join(grader_path+ '___temp'))
            zip_ref.close()



    i = 0
    while os.path.exists(target + str(i)):
        i += 1
    target += str(i)
    os.makedirs(target)


    if grading:
        field_names=["Display ID","ID","Last Name","First Name","grade","Submission date","Late submission"]
        with open(os.path.join(source, 'grades.csv'), 'r') as infile:
            lines = infile.read().split('\n')
            master_lines_list = [[x.strip('\"') for x in line.split('\",')] for line in lines]
            header_list = master_lines_list[:3]
            master_lines_list = master_lines_list[3:-1]
            master_grades = OrderedDict()
            for l in master_lines_list:
                master_grades[l[0]] = 0.

        grades_stats = np.zeros((len(graders),len(students)))
        all_grades = OrderedDict()
        all_grades['master'] = master_grades
        for i, grader in enumerate(graders):
            with open(os.path.join(hw_dir, grader, 'grades.csv'), 'r') as infile:
                lines = infile.read().split('\n')
            grader_total = np.zeros((len(students)))
            lines_list = [[x.strip('\"') for x in line.split(',')] for line in lines][3:]
            if lines_list[-1] == ['']:
                lines_list = lines_list[:-1]
            subgrades = OrderedDict()
            all_grades[grader] = subgrades

            for line in lines_list:
                try: subgrades[line[0]] = line[4]
                except IndexError:
                    print(line)
            for j, (net_id, master_grade) in enumerate(master_grades.items()):
                try:
                    if subgrades[net_id] == "":
                        sg = 0
                    else:
                        sg = float(subgrades[net_id])
                    grader_total[j] = sg
                    master_grades[net_id] = str(float(master_grade) + sg)
                except KeyError:
                    import ipdb; ipdb.set_trace()
            grader_mean = np.mean(grader_total)
            grader_std = np.std(grader_total)
            grader_median = np.median(grader_total)
            grades_stats[i] = grader_total
            #import ipdb; ipdb.set_trace()
            print("Problem {}: median = {:.2f}, mean = {:.2f}, std = {:.2f}".format(grader, grader_median, grader_mean, grader_std))

        overall_median = np.median(np.sum(grades_stats, 0), 0)
        overall_mean = np.mean(np.sum(grades_stats, 0), 0)
        overall_std = np.std(np.sum(grades_stats, 0), 0)
        print("Overall: median = {:.2f}, mean = {:.2f}, std = {:.2f}".format(overall_median, overall_mean, overall_std))

        with open(os.path.join(target, 'grades.csv'), mode='w') as outfile:
            for l in header_list:
                l_ = ['\"' + x + '\"' for x in l]
                out_str = ','.join(l_)
                outfile.write(out_str + '\n')
            for l in master_lines_list:
                net_id = l[0]
                master_grade = master_grades[net_id]
                l[4] = master_grade
                l_ = ['\"' + x + '\"' for x in l]
                out_str = ','.join(l_)
                outfile.write(out_str + '\n')


    if commenting:
        for student in students:
            target_comments = ""
            for grader in graders:
                subgrades = all_grades[grader]
                grader_path = os.path.join(hw_dir, grader)
                net_id = student.split('(')[1].rstrip(')')

                with open(os.path.join(grader_path, student, "comments.txt"), 'r', encoding="latin-1") as f:
                    comments = f.read()
                    target_comments += ('({}) {} points\n'.format(grader, subgrades[net_id]) + comments + '\n\n--------\n\n')


            os.makedirs(os.path.join(target, student))
            with open(os.path.join(target, student, "comments.txt"), 'w', encoding="latin-1") as f:
                f.write(target_comments)

        # zip everything and destroy the evidence

        target_path = os.path.join(target)
        shutil.make_archive(target_path, 'zip', target_path)

        if zipping:
            for grader in graders:
                shutil.rmtree(os.path.join(hw_dir, grader))
            shutil.rmtree(target_path)



if __name__ == "__main__":
    commenting = True
    grading = True
    main(commenting, grading, source, target, hw_dir=hw_dir, graders=graders)
