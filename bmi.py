import sys

height = float(sys.argv[1]) / 100
weight = float(sys.argv[2])
bmi = round(weight / (height ** 2), 2)
print(bmi)
