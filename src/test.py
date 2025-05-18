from functools import cache
import time


@cache
def cached_find_factors(num):
    factors = []
    for i in range(2, num):
        if num // i == num / i:
            factors.append(i)
            # print(f"finding factors of {num}, {i}")
            factors += cached_find_factors(num // i)
    return factors


def find_factors(num):
    factors = []
    for i in range(2, num):
        if num // i == num / i:
            factors.append(i)
            # print(f"finding factors of {num}, {i}")
            factors += find_factors(num // i)
    return factors


start1 = time.time()
for i in range(10000):
    set(find_factors(i) + [1])
    # print(f"finding factors of {i}")
end1 = time.time()
uncached_time = end1 - start1
print(f"Without cache took: {uncached_time}s")
start2 = time.time()
for i in range(10000):
    set(cached_find_factors(i) + [1])
    # print(f"finding factors of {i}")
end2 = time.time()
cached_time = end2 - start2
print(f"With cache took: {cached_time}s")
print(
    f"Cached factorisation is {100 * ((uncached_time - cached_time) / uncached_time)}% faster"
)
