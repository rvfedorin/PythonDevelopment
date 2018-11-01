
# print(f"{192:08b}.{168:08b}.{0:08b}.{0:08b}")
# print(f"{192:08b}.{168:08b}.{128:08b}.{128:08b}")


position = 7
variable = [0, 1]
p = 0
temp = {}
while p <= position:
    temp[p] = []
    for v in variable:
        if p > 0:
            for back_pos in temp[p-1]:
                temp[p].append(f"{back_pos}{v}")
        else:
            temp[p].append(f"{v}")

    p += 1

for i in temp[position]:
    print(i)

print(len(temp[position]))