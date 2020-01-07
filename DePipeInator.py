import sys
import os
import zipfile

NUM_ARGS = 7
USAGE_STRING = ("Usage:  DePipeInator <facility (dir)> <file type> <file version> <start date> " +
                "<end date> <trailing char to remove>\n" +
                "\tEx:  DePipeInator BHTN RETRO 01D 20190901 20190903 |")
HEADER_STRING = "Header line - ignore\n"


def get_sys_args():
    # Usage:  DePipeInator <facility (dir)> <file type> <file version> <start date> <end date> <trailing char to rm>
    args = {}

    if len(sys.argv) < NUM_ARGS:
        print("ERROR: expected " + str(NUM_ARGS) + " args got " + str(len(sys.argv)))
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


def cleanup_file(remove_char, zip_file_name, outfile):
    if not os.path.isfile(zip_file_name):
        return False

    input = open(zip_file_name, "r")
    output = open(outfile, "w")

    # Add the header then read in each line and remove the trailing char if it's there
    output.write(HEADER_STRING)

    for line in input:
        if line[-1] == remove_char:
            output.write(line[:-1])
        else:
            output.write(line)

    return True


def main_function():
    arg_set = get_sys_args()
    print(arg_set)

    start_date = int(arg_set['start_date'])
    stop_date = int(arg_set['stop_date'])

    for index_date in range(start_date, stop_date):
        file_path = get_file_path(arg_set, index_date)
        if not os.path.isfile(file_path):
            # print("ERROR: file '{}' not found".format(file_path), file=sys.stderr)
            print("{} FAIL - missing file".format(file_path))
            continue

        # Unzip the file
        with zipfile.ZipFile(file_path, 'r') as zip:
            try:
                zip.extractall(os.path.dirname(file_path))
            except:
                print("{} FAIL - unable to unzip".format(file_path))
                continue

        base_file_path = file_path.replace(".zip", "")
        if cleanup_file(arg_set['trailing_char'], base_file_path, f"{base_file_path}.out"):
            print("{} PASS".format(file_path))
        else:
            print("{} FAIL - cleanup error")

    return 0


main_function()
