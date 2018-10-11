# ver 1.0.2
# created by Roman Fedorin

import time


def create_log(data_to_file, sity, action):
    this_time = time.localtime()
    this_time_in_my_format = time.strftime("%Y%m%d_%H%M", this_time)
    name_file_log = this_time_in_my_format + '_' + sity + '_' + action
    file_for_log = f'./log/{name_file_log}.txt'

    with open(file_for_log, 'w') as log_file_discr:
        log_file_discr.write('+'*88 + '\n')
        for i in data_to_file:
            log_file_discr.write(i)
        log_file_discr.close()
        print()
        print('LOG FILE CREATED SUCCESSFUL')
