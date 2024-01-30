x = ["0", "1", "2"]
y = ''.join(x)  # converting list into string
z = float(y)
a = sum(float(item) for item in x)
print(a)
