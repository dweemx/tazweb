import csv
import os


def read_table(file, sep='\t', header=True):
    with open(file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        # https://www.kaggle.com/c/titanic/discussion/3224
        if header:
            headers = reader.__next__()
        rows = []

        for row in reader:
            r = dict(zip(headers, row))
            rows.append(r)
        return rows


def write_table(header, content, file_path, _delimiter='\t'):
    with open(file_path, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=_delimiter)
        writer.writerow(header)
        [writer.writerow(r) for r in content]


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
