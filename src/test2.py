flowers = ["Rose", "Lavender"]
subsets = []
for i in range(len(flowers)**2):
    subsets.append([])
    binary = bin(i+1)[1:]
    for digit in binary:
        if digit == "1":
            subsets[-1].append(flowers[i])

print(subsets)