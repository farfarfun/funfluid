import os

path = "/c/d/a1/dfdf/sdfs.txt"
a, b = os.path.splitext(path)
print(a)
print(os.path.splitext(a))
