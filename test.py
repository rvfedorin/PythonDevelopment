
x = 's'
digits = 4 if isinstance(x, str) else 2
print(digits)
print("%0*X" % (digits, ord(x)))
print(f"{ord(x):0{digits}X}")
print(f".{chr(0x7F)}.")
