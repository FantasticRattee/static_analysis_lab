# def calc(a, b):
#     x = 0
#     if a > 0:
#         if b > 0:
#             if a > b:
#                 x = a - b
#             else:
#                 x = b - a
#     return x

def calc(a, b):
    if a <= 0 or b <= 0:
        return 0

    if a > b:
        return a - b
    else:
        return b - a