
x1 = '0b11111111111111111111111100000000'
x2 = '0b11000000101010000000000100000001'

conta = 0
maior = ('', 0)
res = ''
for i in range(2,len(x1)):
    res = res + str(int(x1[i]) & int(x2[i]))
    if int(x1[i]) & int(x2[i]): conta += 1
    else:
        if conta > maior[1]: maior = (x2, conta)
        break

print(maior)