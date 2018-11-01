
# print(f"{192:08b}.{168:08b}.{0:08b}.{0:08b}")
# print(f"{192:08b}.{168:08b}.{128:08b}.{128:08b}")


position = 3
variable = [0, 1]

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


for i in sorted(temp_previous):
    # print(int(i, 2))
    print(i)

