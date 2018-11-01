
# print(f"{192:08b}.{168:08b}.{0:08b}.{0:08b}")
# print(f"{192:08b}.{168:08b}.{128:08b}.{128:08b}")


def combine(position:int, variable:list):
    temp_previous = []
    temp_last = []
    for p in range(position):
        for v in variable:
            if p > 0:
                for back_pos in temp_previous:
                    temp_last.append(f"{back_pos}{v}")
            else:
                temp_last.append(f"{v}")
        temp_previous = temp_last[:]
        temp_last.clear()
    return temp_previous[:]


def combine_yeld(position:int, variable:list):
    temp_previous = []
    temp_last = []
    for p in range(position):
        for v in variable:
            if p > 0:
                for back_pos in temp_previous:
                    temp_last.append(f"{back_pos}{v}")
                    if p == position-1:
                        yield f"{back_pos}{v}"
            else:
                temp_last.append(f"{v}")
        temp_previous = temp_last[:]
        temp_last.clear()


if __name__ == '__main__':

    position = 3
    variable = [0, 1]

    all_variants = combine(position, variable)
    all_yeld = combine_yeld(position, variable)

    for i in all_yeld:
        # print(int(i, 2))
        print(i)

