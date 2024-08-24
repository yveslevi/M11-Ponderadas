import math

def calcular_entropia(probabilidades):
    return -sum(p * math.log2(p) for p in probabilidades if p > 0)

A= 10/20
B= 5/20
C= 3/20
D= 2/20
E= 0/20
F= 0/20

entropia = calcular_entropia([A, B, C, D, E, F])
print(f"Entropia: {entropia} bits")