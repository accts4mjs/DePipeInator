import sys
import os
import zipfile

NUM_ARGS = 7  # Includes script name
USAGE_STRING = ("Usage:  DePipeInator <facility (dir)> <file type> <file version> <start date> " +
                "<end date> <trailing char to remove>\n" +
                "\tEx:  DePipeInator BHTN RETRO 01D 20190901 20190903 |")
HEADER_STRING = "# Header line - ignore\n"


def get_sys_args():
    # Usage:  DePipeInator <facility (dir)> <file type> <file version> <start date> <end date> <trailing char to rm>
    args = {}

    if len(sys.argv) < NUM_ARGS:
        print("ERROR: expected " + str(NUM_ARGS - 1) + " args got " + str(len(sys.argv) - 1))
        print(USAGE_STRING)
        exit(-1)

    args['facility_dir'] = sys.argv[1]
    if not os.path.isdir(args['facility_dir']):
        print("ERROR: " + args['facility_dir'] + " not a valid facility dir")
        print(USAGE_STRING)
        exit(-1)
    args['file_type'] = sys.argv[2]
    args['file_version'] = sys.argv[3]
    args['start_date'] = sys.argv[4]
    args['stop_date'] = sys.argv[5]
    args['trailing_char'] = sys.argv[6]
    if len(args['trailing_char']) > 1:
        print("ERROR: '" + args['trailing_char'] + "' not a single char")
        print(USAGE_STRING)
        exit(-1)

    return args


def get_file_path(data, index_date):
    # Example:  BHTN\20190901\RETRO01D\20190901.BHTN.RETRO01D.zip
    return (f"./{data['facility_dir']}/{index_date}/{data['file_type']}{data['file_version']}" +
            f"/{index_date}.{data['facility_dir']}.{data['file_type']}{data['file_version']}.zip")


def remove_trailing_char(remove_char, zip_file_name, outfile):
    if not os.path.isfile(zip_file_name):
        return False

    input = open(zip_file_name, "r")
    output = open(outfile, "w")

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


def main_function():
    arg_set = get_sys_args()

    start_date = int(arg_set['start_date'])
    stop_date = int(arg_set['stop_date'])

    for index_date in range(start_date, stop_date + 1):
        files_to_remove = []
        original_file_path = get_file_path(arg_set, index_date)
        original_unzipped_file_path = original_file_path.replace(".zip", "")

        if not os.path.isfile(original_file_path):
            # print("ERROR: file '{}' not found".format(file_path), file=sys.stderr)
            print("{} FAIL - missing file".format(original_file_path))
            continue

        # Unzip the original file
        with zipfile.ZipFile(original_file_path, 'r') as zip:
            files_to_remove.append(original_unzipped_file_path)
            try:
                zip.extractall(os.path.dirname(original_file_path))
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

        if not remove_trailing_char(arg_set['trailing_char'], f"{original_unzipped_file_path}.orig", original_unzipped_file_path):
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

        with zipfile.ZipFile(os.path.basename(original_file_path), 'w') as zip:
            try:
                zip.write(os.path.basename(original_unzipped_file_path))
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
            print("{} FAIL - CRITICAL ERROR, unable to chdir to {} the previous path.  Aborting.  No cleanup.".format(original_file_path, curr_path))
            exit(-1)

        cleanup_temp_files(files_to_remove)  # Do not revert orig file as new file is now in place
        print("{} PASS".format(original_file_path))

    return 0


main_function()
