from my_helper import *

# Check usage
test = "CHECK USAGE"
expected = ("ERROR: unexpected # of args\n"
            "Usage:  UnDePipeInator <facility (dir)> <file type> <file version> <start date> " +
            "<end date> <-r <trailing char to remove> | -a <field name> <position> | -u>\n" +
            "\t-r = remove trailing char - char must be provided\n" +
            "\t-u = undo by removing new file and renaming .orig file to original\n" +
            "\t-a = add extra field name in a specific position to file in zip and zip name\n"
            "\tEx:  DePipeInator BHTN RETRO 01D 20190901 20190903 -r '|'\n" +
            "\tEx:  DePipeInator BHTN COLLECT 01D 20190901 20190903 -u" +
            "\tEx:  DePipeInator BHTN PMTS 01D 20190901 20190903 -a HIST 3")
result = my_call_python("DePipeInator.py")
my_tdd(result, expected, test)

test = "REMOVE '|' CHAR"
expected = "./BHTN/20190831/20190831.BHTN.RETRO01D.zip FAIL - missing " \
           "file\n./BHTN/20190901/20190901.BHTN.RETRO01D.zip PASS\n./BHTN/20190902/20190902.BHTN.RETRO01D.zip FAIL - " \
           "missing file\n./BHTN/20190903/20190903.BHTN.RETRO01D.zip FAIL - missing file"
result = my_call_python("DePipeInator.py BHTN RETRO 01D 20190831 20190903 -r |")
#print(f"'{expected}'")
#print(f"'{result}'")
my_tdd(result, expected, test)

test = "UNDO"
expected = "./BHTN/20190831/20190831.BHTN.RETRO01D.zip FAIL - missing .orig " \
           "file\n./BHTN/20190901/20190901.BHTN.RETRO01D.zip PASS\n./BHTN/20190902/20190902.BHTN.RETRO01D.zip FAIL - " \
           "missing .orig file\n./BHTN/20190903/20190903.BHTN.RETRO01D.zip FAIL - missing .orig file"
result = my_call_python("DePipeInator.py BHTN RETRO 01D 20190831 20190903 -u")
#print(f"'{expected}'")
#print(f"'{result}'")
my_tdd(result, expected, test)

test = "RENAME FILE"
expected = "n/a"
result = my_call_python("DePipeInator.py BHTN PMTS 01D 20190831 20190903 -a HIST 3")
#print(f"'{expected}'")
#print(f"'{result}'")
my_tdd(result, expected, test)
