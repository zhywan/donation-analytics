from sys import argv
import os

def read_percentile(percentile_path):
    with open(percentile_path, 'r') as f:
        percentile_str = f.readline().rstrip("\n")
        percentile = int(percentile_str)
    return percentile

def valid_field(field_value,field_name):
    if field_name == 'OTHER_ID':
        if field_value != '':
            return 0
    else:
        if field_value == '':
            return 0
        if field_name == 'TRANSACTION_DT':
            if not field_value.isdigit(): # not digits
                return 0
            if len(field_value) != 8: # not 8 digits
                return 0
            month = int(field_value[0:2])
            if month <1 or month > 12: #not a valid month
                return 0
            day = int(field_value[2:4])
            if day < 1 or day > 31: # not a valid day
                return 0
            year = int(field_value[4:])
            if year < 1776 or year > 2018: # not a valid voting year
                return 0
        if field_name == 'ZIP_CODE':
            if not field_value.isdigit(): # not digits
                return 0
            if len(field_value) < 5 or len(field_value) > 9: # fewer than 5 digits or more than 9 digits
                return 0
        if field_name == 'NAME':
            names = field_value.split(", ")
            if len(names) != 2: # no first name or no last name
                return 0
            if not names[0] or not names[1]: # first name or last name is emtpy
                return 0
    return 1

def valid_fields(fields):
    return valid_field(fields[0],'CMTE_ID') \
           and valid_field(fields[1],'NAME') \
           and valid_field(fields[2],'ZIP_CODE') \
           and valid_field(fields[3],'TRANSACTION_DT') \
           and valid_field(fields[4],'TRANSACTION_AMT') \
           and valid_field(fields[5],'OTHER_ID')

def compute_percentile(lst, percentile):
    ordinal_rank = percentile*len(lst)//100+1
    return lst[ordinal_rank-1]

def earlier_transaction_dt(dt1, dt2): #return 1 if dt1 earlier than dt2
    # compare year
    year1 = int(dt1[4:])
    year2 = int(dt2[4:])
    if year1 < year2:
        return 1
    if year1 > year2:
        return -1
    # compare month
    month1 = int(dt1[0:2])
    month2 = int(dt2[0:2])
    if month1 < month2:
        return 1
    if month1 > month2:
        return -1
    # compare day
    day1 = int(dt1[2:4])
    day2 = int(dt2[2:4])
    if day1 < day2:
        return 1
    if day1 > day2:
        return -1
    return 0

def binary_search(lst, element, start, end):
    if start == end:
        if lst[start]> element:
            return start
        else:
            return start + 1
    if start > end:
        return start
    mid = (start + end) / 2
    if lst[mid] < element:
        return binary_search(lst, element, mid+1, end)
    elif lst[mid] > element:
        return binary_search(lst, element, start, mid-1)
    else:
        return mid

def insert_sorted_list(lst, element):
    position = binary_search(lst, element, 0, len(lst)-1)
    lst = lst[:position] + [element] + lst[position:]
    return lst

if __name__ == '__main__':

    if len(argv) != 4:
        print('Not enough inputs! Using default...\n')
        itcont_filename = "input/itcont.txt"
        percentile_filename = "input/percentile.txt"
        out_filename = "output/repeat_donors.txt"
    else:
        itcont_filename = argv[1]
        percentile_filename = argv[2]
        out_filename = argv[3]
    my_path = os.path.abspath(os.path.dirname(__file__))
    parent_path = my_path[:-3]
    print('parent_path: '+parent_path)
    itcont_path = os.path.join(parent_path, itcont_filename)
    print('itcont_path: '+itcont_path)
    percentile_path = os.path.join(parent_path, percentile_filename)
    print('percentile_path: ' + percentile_path)
    out_path = os.path.join(parent_path, out_filename)
    print('out_path: ' + out_path)
    donor_dict={}
    recipient_dict={}
    percentile = read_percentile(percentile_path)
    with open(itcont_path, 'r') as f:
        with open(out_path, 'w') as out:
            for line in f.readlines():
                columns = line.rstrip("\n").split("|")
                cmte_id = columns[0]
                name = columns[7]
                zip_code = columns[10]
                transaction_dt = columns[13]
                transaction_amt = columns[14]
                other_id = columns[15]
                if not valid_fields([cmte_id, name, zip_code, transaction_dt, transaction_amt, other_id]):
                    continue
                # update donor dictionary
                zip5 = zip_code[:5]
                key = zip5 + name
                if key not in donor_dict: # 1st time donor
                    donor_dict[key] = [cmte_id, transaction_dt, transaction_amt]
                else: # repeat donor
                    value = donor_dict[key]
                    if earlier_transaction_dt(transaction_dt, value[1])==1:
                        donor_dict[key] = [cmte_id, transaction_dt, transaction_amt]
                        cmte_id, transaction_dt, transaction_amt = value[0], value[1], value[2]
                    # update recipient dictionary
                    year = transaction_dt[4:]
                    key2 = year + zip5 + cmte_id
                    if key2 not in recipient_dict: # 1st time recipient
                        recipient_dict[key2] = [int(transaction_amt)]
                    else:
                        recipient_dict[key2] = insert_sorted_list(recipient_dict[key2], int(transaction_amt))
                    percentile_amt = compute_percentile(recipient_dict[key2], percentile)
                    total_amt = sum(recipient_dict[key2])
                    total_num = len(recipient_dict[key2])
                    output_str=[cmte_id, zip5, year, str(percentile_amt), str(total_amt), str(total_num)]
                    out.write('|'.join(output_str)+'\n')

		#print(donor_dict)
		#print(recipient_dict)
		#a=raw_input()
