_list = [9, 8, 7, 6, 5, 3, 4, 2, 1]
n = len(_list) - 1
for i in range(n):
    for j in range(n - i):
        if _list[j] > _list[j+1]:
            _list[j], _list[j+1] = _list[j+1], _list[j]

print(_list)
