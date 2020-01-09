import sys
import os
import zipfile
from datetime import timedelta, date

NUM_ARGS = [8, 9, 10]  # Includes script name
USAGE_STRING = ("Usage:  DePipeInator <facility (dir)> <file type> <file version> <suffix> <start date> " +
                "<end date> <-m | -r <trailing char to remove> | -a <field name> <position> | -u>\n" +
                "\t-m = scan range of directories for missing files\n" +
                "\t-r = remove trailing char - char must be provided\n" +
                "\t-u = undo by removing new file and renaming .orig file to original\n" +
                "\t-a = add extra field name in a specific position to file in zip and zip name\n" +
                "\t\tNOTE: position starts at 0.  Ex: A.B.C  A=0, B=1, C=2"
                "\tNOTE: <suffix> can be an empty char ''"
                "\tEx:  DePipeInator BHTN RETRO 01D 20190901 20190903 -r '|'\n" +
                "\tEx:  DePipeInator BHTN COLLECT 01D 20190901 20190903 -u" +
                "\tEx:  DePipeInator BHTN PMTS 01D 20190901 20190903 -a HIST 3")
HEADER_STRING = "# Header line - ignore\n"
STATE_REMOVE = 0
STATE_UNDO = 1
STATE_ADD = 2
STATE_MISSING = 3


def convert_to_date(date_str):
    result_date = None
    # Dates need to be in YYYYMMDD format
    if len(date_str) != 8:
        print(f"ERROR: {sys.argv[4]} invalid date format.  Should be YYYYMMDD")
        print(USAGE_STRING)
        exit(0)
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    try:  # Test that date is valid
        result_date = date(year, month, day)
    except ValueError:
        print(f"ERROR: {sys.argv[4]} invalid date format.  Should be YYYYMMDD")
        print(USAGE_STRING)
        exit(0)

    return result_date


def get_sys_args():
    # Usage:  DePipeInator <facility (dir)> <file type> <file version> <start date> <end date> <trailing char to rm>
    args = {}
    num_args = len(sys.argv)

    if num_args not in NUM_ARGS:
        print("ERROR: unexpected # of args")
        print(USAGE_STRING)
        exit(0)

    args['facility_dir'] = sys.argv[1]
    if not os.path.isdir(args['facility_dir']):
        print("ERROR: " + args['facility_dir'] + " not a valid facility dir")
        print(USAGE_STRING)
        exit(0)
    args['file_type'] = sys.argv[2]
    args['file_version'] = sys.argv[3]
    args['suffix'] = sys.argv[4]
    args['start_date'] = convert_to_date(sys.argv[5])
    args['stop_date'] = convert_to_date(sys.argv[6])
    if num_args == 8 and sys.argv[7] == "-m":
        args['function'] = STATE_MISSING
    elif num_args == 8 and sys.argv[7] == "-u":
        args['function'] = STATE_UNDO
    elif num_args == 9 and sys.argv[7] == "-r":  # Make sure you have enough args
        args['function'] = STATE_REMOVE
        args['trailing_char'] = sys.argv[8]
        if len(args['trailing_char']) > 1:
            print("ERROR: '" + args['trailing_char'] + "' not a single char")
            print(USAGE_STRING)
            exit(0)
    elif num_args == 10 and sys.argv[7] == "-a":  # Make sure you have enough args
        args['function'] = STATE_ADD
        args['field_name'] = sys.argv[8]
        args['field_position'] = int(sys.argv[9])
        if args['field_position'] < 0:
            print("ERROR: '" + args['field_position'] + "' not a valid position")
            print(USAGE_STRING)
            exit(0)
    else:
        print("ERROR: wrong syntax")
        print(USAGE_STRING)
        exit(0)

    return args


def get_file_path(data, index_date):
    # Example:  BHTN\20190901\20190901.BHTN.RETRO01D.zip or BHTN\20190901\20190901.BHTN.PMTS01D.TXT.zip
    if data['suffix'] != "":
        return (f"./{data['facility_dir']}/{index_date}" +
                f"/{index_date}.{data['facility_dir']}.{data['file_type']}{data['file_version']}." +
                f"{data['suffix']}.zip")
    else:
        return (f"./{data['facility_dir']}/{index_date}" +
                f"/{index_date}.{data['facility_dir']}.{data['file_type']}{data['file_version']}.zip")


def remove_trailing_char(remove_char, zip_file_name, outfile):
    if not os.path.isfile(zip_file_name):
        return False

    input = open(zip_file_name, "r")
    output = open(outfile, "w", newline='\n')

    # Add the header then read in each line and remove the trailing char if it's there
    output.write(HEADER_STRING)

    for line in input:
        if len(line) < 2:
            output.write(line)
            continue

        if line[-2] == remove_char:
            output.write(f"{line[:-2]}\n")
        else:
            output.write(line)

    return True


def cleanup_temp_files(file_list):
    for curr_file in file_list:
        try:
            os.remove(curr_file)
        except:
            continue  # Silent fail


def revert_orig_file(orig_file):
    try:
        os.rename(orig_file, orig_file.replace(".orig", ""))
    except:
        return  # Silent fail


def date_time_iterator(from_date, to_date):
    if from_date > to_date:
        return
    else:
        while from_date <= to_date:
            yield from_date
            from_date = from_date + timedelta(days=1)
        return


def run_remove_trailing_char(arg_set):
    for index_date in date_time_iterator(arg_set['start_date'], arg_set['stop_date']):
        index_str = str(index_date).replace("-", "")

        files_to_remove = []
        original_file_path = get_file_path(arg_set, index_str)
        original_unzipped_file_path = original_file_path.replace(".zip", "")

        if not os.path.isfile(original_file_path):
            # print("ERROR: file '{}' not found".format(file_path), file=sys.stderr)
            print("{} FAIL - missing file".format(original_file_path))
            continue

        # Unzip the original file
        with zipfile.ZipFile(original_file_path, 'r') as my_zip_file:
            files_to_remove.append(original_unzipped_file_path)
            try:
                my_zip_file.extractall(os.path.dirname(original_file_path))
            except:
                print("{} FAIL - unable to unzip".format(original_file_path))
                cleanup_temp_files(files_to_remove)
                continue

        # Rename original extracted file and zip file
        files_to_remove.append(f"{original_unzipped_file_path}.orig")
        try:
            os.rename(original_file_path, f"{original_file_path}.orig")
            os.rename(original_unzipped_file_path, f"{original_unzipped_file_path}.orig")
        except:
            print("{} FAIL - unable to rename original files".format(original_file_path))
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue

        if not remove_trailing_char(arg_set['trailing_char'], f"{original_unzipped_file_path}.orig",
                                    original_unzipped_file_path):
            print("{} FAIL - cleanup error".format(original_file_path))
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue

        # Zip new file and remove temp files (both new and original but leave original zip)
        # NOTE:  Need to chdir to path of zip file otherwise new zip file doesn't contain just the file it contains the
        #       full path to the file inside the zip (not desired).
        curr_path = os.path.abspath(".")
        try:
            os.chdir(os.path.dirname(original_file_path))
        except:
            print("{} FAIL - unable to chdir to zip file dir".format(original_file_path))
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue

        try:
            with zipfile.ZipFile(os.path.basename(original_file_path), 'w', compression=zipfile.ZIP_DEFLATED) as my_zip_file:
                my_zip_file.write(os.path.basename(original_unzipped_file_path))
        except:
            print("{} FAIL - unable to zip new file".format(original_file_path))
            os.chdir(curr_path)
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue
        try:
            os.chdir(curr_path)
        except:
            # NOTE: If chdir back to original dir fails then we have a critical error and should abort
            print("{} FAIL - CRITICAL ERROR, unable to chdir to {} the previous path.  Aborting.  No cleanup.".format(
                original_file_path, curr_path))
            exit(0)

        cleanup_temp_files(files_to_remove)  # Do not revert orig file as new file is now in place
        print("{} PASS".format(original_file_path))

    return 0


def run_undo(arg_set):
    for index_date in date_time_iterator(arg_set['start_date'], arg_set['stop_date']):
        index_str = str(index_date).replace("-", "")

        current_file_path = get_file_path(arg_set, index_str)
        original_file_path = current_file_path.replace(".zip", ".zip.orig")

        # Both files should be present.  If .orig missing, stop.  If .zip missing but .orig available, okay to restore
        if not os.path.isfile(original_file_path):
            print("{} FAIL - missing .orig file".format(current_file_path))
            continue

        if os.path.isfile(current_file_path):
            # Remove the current .zip file
            try:
                os.remove(current_file_path)
            except:
                print(f"{current_file_path} FAIL - unable to remove current .zip file.")
                continue

        # Move .orig file back
        try:
            os.rename(original_file_path, current_file_path)
        except:
            print(f"{current_file_path} FAIL - unable to rename .orig file")
            continue

        print(f"{current_file_path} PASS")

    return 0


def get_file_path_add_field(data, index_date):
    # Original file path Ex:  BHTN\20190901\20190901.BHTN.RETRO01D.zip
    # Field gets added in the basename.  Positions are 0 based and separated by a period.
    base_path = f"./{data['facility_dir']}/{index_date}/"
    if data['suffix'] != "":
        name_list = [str(index_date), data['facility_dir'], f"{data['file_type']}{data['file_version']}",
                     data['suffix']]
    else:
        name_list = [str(index_date), data['facility_dir'], f"{data['file_type']}{data['file_version']}"]
    name_list.insert(data['field_position'], data['field_name'])
    delimiter = "."
    return base_path + delimiter.join(name_list) + ".zip"


def add_field_to_name(arg_set):
    for index_date in date_time_iterator(arg_set['start_date'], arg_set['stop_date']):
        index_str = str(index_date).replace("-", "")

        files_to_remove = []
        original_file_path = get_file_path(arg_set, index_str)
        original_unzipped_file_path = original_file_path.replace(".zip", "")
        new_file_path = get_file_path_add_field(arg_set, index_str)
        new_unzipped_file_path = new_file_path.replace(".zip", "")

        if not os.path.isfile(original_file_path):
            # print("ERROR: file '{}' not found".format(file_path), file=sys.stderr)
            print("{} FAIL - missing original file".format(original_file_path))
            continue

        # Unzip the original file
        with zipfile.ZipFile(original_file_path, 'r') as my_zip_file:
            files_to_remove.append(original_unzipped_file_path)
            try:
                my_zip_file.extractall(os.path.dirname(original_file_path))
            except:
                print("{} FAIL - unable to unzip original file".format(original_file_path))
                cleanup_temp_files(files_to_remove)
                continue

        # Rename original zip file to save in case need to revert
        # Rename extracted file to new file name
        files_to_remove.append(new_unzipped_file_path)
        try:
            os.rename(original_file_path, f"{original_file_path}.orig")
            os.rename(original_unzipped_file_path, new_unzipped_file_path)
        except:
            print("{} FAIL - unable to rename original file or rename new file".format(original_file_path))
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue

        # Zip new file and remove temp files
        # NOTE:  Need to chdir to path of zip file otherwise new zip file doesn't contain just the file it contains the
        #       full path to the file inside the zip (not desired).
        curr_path = os.path.abspath(".")
        try:
            os.chdir(os.path.dirname(original_file_path))
        except:
            print("{} FAIL - unable to chdir to zip file dir".format(original_file_path))
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue

        try:
            with zipfile.ZipFile(os.path.basename(new_file_path), 'w', compression=zipfile.ZIP_DEFLATED) as my_zip_file:
                my_zip_file.write(os.path.basename(new_unzipped_file_path))
        except:
            print("{} FAIL - unable to zip new file".format(original_file_path))
            os.chdir(curr_path)
            cleanup_temp_files(files_to_remove)
            revert_orig_file(original_file_path)
            continue
        try:
            os.chdir(curr_path)
        except:
            # NOTE: If chdir back to original dir fails then we have a critical error and should abort
            print("{} FAIL - CRITICAL ERROR, unable to chdir to {} the previous path.  Aborting.  No cleanup.".format(
                original_file_path, curr_path))
            exit(0)

        cleanup_temp_files(files_to_remove)  # Do not revert orig file as new file is now in place
        print("{} PASS".format(original_file_path))

    return 0


def check_for_missing_files(arg_set):
    for index_date in date_time_iterator(arg_set['start_date'], arg_set['stop_date']):
        index_str = str(index_date).replace("-", "")

        file_path = get_file_path(arg_set, index_str)

        if not os.path.isfile(file_path):
            print(f"{file_path} FAIL - missing file")
        else:
            print(f"{file_path} PASS")

    return 0


def main_function():
    arg_set = get_sys_args()
    if arg_set['function'] == STATE_REMOVE:
        return run_remove_trailing_char(arg_set)
    elif arg_set['function'] == STATE_UNDO:
        return run_undo(arg_set)
    elif arg_set['function'] == STATE_ADD:
        return add_field_to_name(arg_set)
    elif arg_set['function'] == STATE_MISSING:
        return check_for_missing_files(arg_set)
    else:
        return -1


main_function()
