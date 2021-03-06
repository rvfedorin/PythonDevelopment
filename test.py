
# print(f"{192:08b}.{168:08b}.{0:08b}.{0:08b}")
# print(f"{192:08b}.{168:08b}.{128:08b}.{128:08b}")


def combine(pos: int, variable=None):
    temp_previous = []
    temp_last = []
    if variable is None:
        variable = [0, 1]

    for p in range(pos):
        for v in variable:
            if p > 0:
                for back_pos in temp_previous:
                    temp_last.append(f"{back_pos}{v}")
            else:
                temp_last.append(f"{v}")
        temp_previous = temp_last[:]
        temp_last.clear()
    return temp_previous[:]


def combine_yeld(pos: int, variable=None):
    temp_previous = []
    temp_last = []
    if variable is None:
        variable = [0, 1]

    for p in range(pos):
        for v in variable:
            if p > 0:
                for back_pos in temp_previous:
                    temp_last.append(f"{back_pos}{v}")
                    if p == pos-1:
                        yield f"{back_pos}{v}"
            else:
                temp_last.append(f"{v}")
        temp_previous = temp_last[:]
        temp_last.clear()


if __name__ == '__main__':

    position = 5

    all_variants = combine(position)
    all_yeld = combine_yeld(position)

    # for i in all_variants:
    #     # print(int(i, 2))
    #     print(i)


