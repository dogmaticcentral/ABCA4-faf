from utils.utils import scream


def guess_delimiter(infile_path) -> str:
    ext = infile_path.suffix

    if ext not in [".tsv", ".csv"]:
        print("Please provide the input in either tsv (tab-delimited) or csv (comma-delimited) format.")
        print("(With the extension to match.)")
        print(ext)
        exit(1)
    return "\t" if ext == ".tsv" else ",'"


def list_to_quoted_str(lst: list[str]) -> str:
    if len(lst) == 0:
        return ""
    if len(lst) == 1:
        return f"'{lst[0]}' column"
    string_rep = ", ".join([f"'{s}'" for s in lst[:-1]])
    string_rep += f" and '{lst[-1]}' columns"
    return string_rep


def file_to_list_of_dict(infile, delimiter, obligatory_columns) -> list[dict]:
    inf = open(infile)
    ret_dict_list = []
    header = None
    for line in inf:
        fields = line.rstrip("\n").split(delimiter)
        if len(fields) < len(obligatory_columns):
            continue
        if not header:
            # get rid of double spaces, get rid of flanking whitespace
            header = [(" ".join(str(s).lower().split())).strip().replace("_", " ") for s in fields]
            for column in set(obligatory_columns).difference(header):
                print("I am assuming that this line is the header:")
                print(line)
                print(f"I was expecting to find '{column}' therein")
                exit()
            header = fields
        else:
            if len(fields) != len(header):
                scream(f"the length of the line:\n{fields} does not match the length of the header:\n{header}.")
                exit()
            line_dict = dict(zip(header, fields))
            line_dict["eye"] = line_dict["eye"].upper()
            if line_dict["eye"] not in ["OD", "OS"]:
                print(f"please label the eyes as 'OD' or 'OS' (I am reading {line_dict['eye']})")
                exit(1)
            ret_dict_list.append(line_dict)

    if not header:
        scream(f"no header containing at least {list_to_quoted_str(obligatory_columns)}  found.")
        exit()
    return ret_dict_list
