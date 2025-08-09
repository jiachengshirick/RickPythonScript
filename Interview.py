def priority(op):
    if op in ('+', '-'):
        return 1
    if op in ('*', '/'):
        return 2
    return 0
def calculator(eq):
    opstk = []
    numstk = []
    i = 0

    while i < len(eq):
        if eq[i].isdigit():
            val = 0
            while i < len(eq) and eq[i].isdigit():
                val = val * 10 + int(eq[i])
                i += 1
            numstk.append(val)
        else:
            while(len(eq) != 0 and priority(opstk[-1]) >= priority(eq[i])):
                if len(numstk)>1:
                    right = numstk.pop()
                    left = numstk.pop()
                    opt = opstk.pop()
                    if opt == '+':
                        numstk.append(add(right, left))
                    elif opt == '-':
                        numstk.append(substract(right, left))
                    elif opt == '*':
                        numstk.append(multi(right,left))
                    elif opt == '/':
                        numstk.append(div(right,left))
                opstk.append(eq[i])
        i += 1



def add(x, y):
    return x + y

def substract(x, y):
    return x - y

def multi(x, y):
    return x * y

def div(x, y):
    if y == 0:
        return "Error: should not divided by zero is not allowed"
    else:
        return x / y
calculator("1+2*3")
# "1*2+3"