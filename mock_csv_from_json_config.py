import argparse
import datetime
import sys
import json
import time
from faker import Faker

# Global run variables
separator = ','
default_file_name = 'mock_csv_{datetime}.csv'
default_row_num = 20
faker = Faker()
# System arguments to determine script behavior
parser = argparse.ArgumentParser()
parser.add_argument('--d', default=',', help='Character to seperate the values of the file')
parser.add_argument('--p', default='config_files.profile',
                    help='Profile file which contains multiple json csv configurations')
parser.add_argument('--j', default=None, help='Specific json csv configuration file to generate one csv file')
sys_args = parser.parse_args()


# Function to generate a delimited string from the values of the passed in list
def list_to_csv_line(value_list, output_separator=separator):
    str_value_list = [str(word) for word in value_list]
    return ''.join(output_separator.join(str_value_list),'\n')


# Function to generate a random value from a list of user specified values - similar to ENUM
def random_value_from_list(value_list):
    str_value_list = [str(word) for word in value_list]
    return faker.words(1, str_value_list, True)[0]


# Add all the values of the specified columns together and return the final value
def add_column_values(row_dict, desired_columns):
    result = 0
    for column in desired_columns:
        result += row_dict.get(column, 0)
    return result


# Find the difference of all the values of the specified columns together and return the final value
def diff_column_values(row_dict, desired_columns):
    result = 0
    for column in range(len(desired_columns)):
        column_name = desired_columns[column]
        if column == 0:
            result = row_dict.get(column_name, 0)
        else:
            result -= row_dict.get(column_name, 0)
    return result


# Function to generate the csv file from the json configuration
def generate_csv_from_json_config(file_name, row_num, columns, specified_separator):
    output_file_name = file_name if file_name is not None else default_file_name.format(
        datetime=datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f'))
    output_row_num = row_num if row_num is not None and isinstance(row_num, int) else default_row_num
    output_separator = specified_separator if specified_separator is not None else separator
    column_list = list(columns.keys())
    config_list = list(columns.values())
    output_str = list_to_csv_line(column_list, output_separator)
    "".join(
        [list_to_csv_line(generate_random_csv_line_from_config(column_list, config_list, row, output_row_num),
                                       output_separator)
             for row in range(output_row_num)])
    # for row in range(output_row_num):
    #     "".join(output_str, list_to_csv_line(generate_random_csv_line_from_config(column_list, config_list, row, output_row_num),
    #                                    output_separator))
    open(output_file_name, 'w').write(output_str.strip())


# Generate a row of random data based off of the json configuration file
def generate_random_csv_line_from_config(column_list, config_list, row_num, max_rows):
    random_row = {}
    for column in range(len(column_list)):
        column_name = column_list[column]
        column_config = config_list[column]
        column_type = column_config.get('type')
        column_set_values = column_config.get('values')
        if column_type is None:
            print('JSON file not properly formatted')
            exit(1)
        elif column_set_values is not None and column_type == 'enum' and column_set_values:
            random_row[column_name] = random_value_from_list(column_set_values)
        elif column_set_values is not None and column_type == 'ordered_enum' and column_set_values:
            rep = column_config.get('rep', 1)
            random_row[column_name] = column_set_values[( row_num//rep) % len(column_set_values)]
        elif column_type == 'seq':
            offset = column_config.get('offset', 0)
            step = column_config.get('step', 1)
            max = column_config.get('max_value', sys.maxsize)
            rep = column_config.get('rep', 1)
            random_row[column_name] = ( (row_num // rep )*step + offset) % max
        elif column_type == 'int':
            random_row[column_name] = faker.pyint(
                min_value=column_config.get('min_value', (-sys.maxsize - 1)) if column_config.get(
                    'min_value') is not None else (-sys.maxsize - 1),
                max_value=column_config.get('max_value', sys.maxsize) if column_config.get(
                    'max_value') is not None else sys.maxsize,
                step=column_config.get('step', 1) if column_config.get('step') is not None else 1)
        elif column_type == 'decimal':
            random_row[column_name] = faker.pydecimal(left_digits=column_config.get('left_digits'),
                                                      right_digits=column_config.get('right_digits'),
                                                      positive=column_config.get('positive'),
                                                      min_value=column_config.get('min_value'),
                                                      max_value=column_config.get('max_value'))
        elif column_type == 'float':
            random_row[column_name] = faker.pyfloat(left_digits=column_config.get('left_digits'),
                                                    right_digits=column_config.get('right_digits'),
                                                    positive=column_config.get('positive'),
                                                    min_value=column_config.get('min_value'),
                                                    max_value=column_config.get('max_value'))
        elif column_type == 'sum':
            random_row[column_name] = add_column_values(random_row, column_config.get('columns'))
        elif column_type == 'diff':
            random_row[column_name] = diff_column_values(random_row, column_config.get('columns'))
        else:
            print('Unsupported column_type, defaulting to empty string')
            random_row[column_name] = ''
    return random_row.values()


# If a custom delimiter is specified reassign the seperator value
if sys_args.d != ',':
    separator = sys_args.d
# If a specific json config file is not specified then default to reading a profile file to generate multiple mock files
if sys_args.j is None:
    profile_files = [file.strip() for file in open(sys_args.p, 'r').readlines()]
    for file in profile_files:
        start_time = time.time()
        config_file_str = open(file, 'r')
        config_file_dict = json.load(config_file_str)
        generate_csv_from_json_config(config_file_dict.get('file_name'), config_file_dict.get('rows'),
                                      config_file_dict.get('columns'), config_file_dict.get('separator'))
        print('{file} Creation Execution Time: {time}s'.format(file=file, time=(time.time() - start_time)))
# If a file is specified then override default behavior and generate one specific mock file
elif sys_args.j:
    start_time = time.time()
    config_file_str = open(sys_args.j, 'r')
    config_file_dict = json.load(config_file_str)
    generate_csv_from_json_config(config_file_dict.get('file_name'), config_file_dict.get('rows'),
                                  config_file_dict.get('columns'), config_file_dict.get('separator'))
    print('{file} Config Creation Time: {time}s'.format(file=sys_args.j, time=(time.time() - start_time)))
