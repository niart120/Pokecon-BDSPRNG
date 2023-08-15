import numpy as np
from functools import reduce
from bisect import bisect

def get_zero(size=32):
    return np.zeros((size,size), dtype="uint8")

def get_identity(size=32):
    return np.identity(size,dtype="uint8")

def get_shift(n,size=32):
    return np.eye(size,k=n,dtype="uint8")

def get_trans():
    t11,t12,t13,t14 = get_zero(),get_identity(),get_zero(),get_zero()
    t21,t22,t23,t24 = get_zero(),get_zero(),get_identity(),get_zero()
    t31,t32,t33,t34 = get_zero(),get_zero(),get_zero(),get_identity()
    t41,t42,t43,t44 = (get_identity()^get_shift(-8))@(get_identity()^get_shift(11)),get_zero(),get_zero(),get_identity()^get_shift(-19)

    
    trans = np.block([
        [t11,t12,t13,t14],
        [t21,t22,t23,t24],
        [t31,t32,t33,t34],
        [t41,t42,t43,t44],
        ])

    return trans

def gauss_jordan(mat,vec:list):
    """Aをmat(F_2上の行列), vecをb(ベクトル)として, Ax=bを満たすようなベクトルxを求める.

    Args:
        mat (_type_): 係数行列
        vec (list): 右辺定数

    Returns:
        _type_: _description_
    """
    r,c = mat.shape

    bitmat = [list2bitvec(mat[i]) for i in range(r)]

    res = [d for d in vec]
    #forward elimination
    pivot = 0
    for i in range(c):
        isfound = False
        for j in range(i,r):
            if isfound:
                check = 1<<(c-i-1)
                if bitmat[j]&check==check:
                    bitmat[j] ^= bitmat[pivot]
                    res[j] ^= res[pivot]
            else:
                check = 1<<(c-i-1)
                if bitmat[j]&check==check:
                    isfound = True
                    bitmat[j],bitmat[pivot] = bitmat[pivot],bitmat[j]
                    res[j],res[pivot] = res[pivot],res[j]
        if isfound:
            pivot += 1

    for i in range(c):
        check = 1<<(c-i-1)
        if bitmat[i]&check == 0:
            return None
    
    #backward assignment
    for i in range(1,c)[::-1]:
        check = 1<<(c-i-1)
        for j in range(i)[::-1]:
            if bitmat[j]&check==check:
                bitmat[j] ^= bitmat[i]
                res[j] ^= res[i]
    return res[:c]

def bitvec2list(bitvec,size=128):
    lst = [(bitvec>>i)%2 for i in range(size)]
    return lst[::-1]

def list2bitvec(lst):
    bitvec = reduce(lambda p,q: (int(p)<<1)|int(q),lst)
    return bitvec

def reverese_float_range(f:float,mi:float,ma:float) -> int:
    norm_f = (ma-f)/(ma-mi)
    norm_i = int(norm_f*8388607.0)
    return int(norm_f*8388607.0)&0x7fffff

def get_raw_int(rand:float, munchlax_blink = 0.285) -> int:
    r = 12.0 - (rand - munchlax_blink)
    if r<0:
        return 0

    raw = reverese_float_range(rand, 3.0 + munchlax_blink, 12.0 + munchlax_blink)
    raw = 0x7F_FFFF if raw > 0x7F_FFFF else raw
    
    return raw

def count_confidence_bits(rand:int, epsilon:int):
    for i in list(range(23))[::-1]:
        mask = 1 << i
        r = rand & (2 * mask -1)

        diff = mask - r if mask > r else r - mask
        if diff <= epsilon:
            return 22 - i

    return 22