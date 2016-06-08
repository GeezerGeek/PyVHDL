#-------------------------------------------------------------------------------
#
#  std_logic_1164.py  -  12/21/15
#
#  Python equivalent of std_logic_1164.vhd 
#
#-------------------------------------------------------------------------------

from Sim.std import StdLogic, StdLogicVector

# Character to enumeration id
encode = {'U':0, 'X':1, '0':2, '1':3, 'Z':4, 'W':5, 'L':6, 'H':7, '-':8,
          'u':0, 'x':1, 'z':4, 'w':5, 'l':6, 'h':7
}

encode_table = encode

# Enumeration id to character
decode = 'UX01ZWLH-'

decode_table = decode

# Logical function look-up tables

and_table = (
    (0, 0, 2, 0, 0, 0, 2, 0, 0),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (2, 2, 2, 2, 2, 2, 2, 2, 2),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (2, 2, 2, 2, 2, 2, 2, 2, 2),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1) 
)

or_table = (
    (0, 0, 0, 3, 0, 0, 0, 3, 0),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (3, 3, 3, 3, 3, 3, 3, 3, 3),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (3, 3, 3, 3, 3, 3, 3, 3, 3),
    (0, 1, 1, 3, 1, 1, 1, 3, 1) 
)

xor_table = (
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 3, 2, 1, 1, 3, 2, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 3, 2, 1, 1, 3, 2, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1) 
)


# Convert encoded StdLogic value to add_table index
add_table_index = (2,2,0,1,2,2,0,1,2)

# Table for addition: add_table[a][b][c] returns [sum, carry] 
add_table = (
    (               # A = 0
        (               # B = 0
            ([2,2]),        # C = 0
            ([3,2]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = 1
        (               # B = 0
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([2,3]),        # C = 0
            ([3,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = X
        (               # B = 0
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
)

def sl_sum(a, b, c):
    return add_table[add_table_index[a]][add_table_index[b]][add_table_index[c]]

sum_table = sl_sum

# Table for subtraction: sub_table[a][b][c] returns [difference, carry] 
sub_table = (
    (               # A = 0
        (               # B = 0
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([2,3]),        # C = 0
            ([3,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = 1
        (               # B = 0
            ([2,2]),        # C = 0
            ([3,2]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = X
        (               # B = 0
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
)

def sl_diff(a, b, c):
    return sub_table[add_table_index[a]][add_table_index[b]][add_table_index[c]]

diff_table = sl_diff

not_table = (0, 1, 3, 2, 1, 1, 3, 2, 1)

# Convert 9-level logic to 4-level logic for VCD dump

to_x01z = 'xx01zx01x'

X01Z_table = to_x01z 
    
#------------------------------------------------------------------------------
#
# Functions for the unified interface for StdLogic, StdLogicVector, SLVRange 

def unary_op(table, a):
    # encode, decode, to_X01Z, not        
    return [table[x] for x in a]

#----

def binary_op(table, a, b):       
    return [table[x][y] for x,y in zip(a,b)]

#----

def arith_op(table, a, b):
    
    carry = encode['0']
    result = []
    for i in range(len(a)):
        q,carry = table(a[i], b[i], carry)
        result.append(q)
    
    return result

#-------------------------------------------------------------------------------
#
# Subset of functions as defined in std_logic_1164
#
# The function doc-string is the unique signature of the function that follows 
# "CALL FUNCTION" in the design.txt file.      


def func0(a, b):
    """"="(CONSTANT A : STD_ULOGIC, CONSTANT B : STD_ULOGIC) RETURN BOOLEAN"""
    return a.getVal() == b.getVal()


def func1(a, b):
    """"AND"(CONSTANT A : BOOLEAN, CONSTANT B : BOOLEAN) RETURN BOOLEAN"""
    return a and b

def func2(L, R):
    """"="(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN BOOLEAN"""
    """"="(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN BOOLEAN"""
    return L.getVal() == R.getVal()

def func3(a, b):
    """"OR"(CONSTANT A : BOOLEAN, CONSTANT B : BOOLEAN) RETURN BOOLEAN"""
    return a or b

def func4(L, R):
    """"+"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : INTEGER) RETURN STD_LOGIC_VECTOR"""
    
    sum = []
    c = 2   # Equivalent to encode('0')         
    result = L.new()
    
    for x, y in zip(L.int2SLV(R), L._val):
        q,c = add_table[add_table_index[x]][add_table_index[y]][add_table_index[c]]
        sum.append(q)
    
    result._val = sum 
    return result

def func5(L, R):
    """"+"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    
    sum = []
    c = 2   # Equivalent to encode('0')         
    result = L.new()
    
    for x, y in zip(R._val, L._val):
        q,c = add_table[add_table_index[x]][add_table_index[y]][add_table_index[c]]
        sum.append(q)
    
    result._val = sum 
    return result

def func6(a, b):
    """"&"(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    return StdLogicVector([str(len(a)+len(b)-1), 'DOWNTO', '0']).setVal(b.getVal() + a.getVal())

def func7(a, b):
    """"&"(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC) RETURN STD_LOGIC_VECTOR"""
    return StdLogicVector([str(len(a)), 'DOWNTO', '0']).setVal(b.getVal() + a.getVal())

def func8(L):
    """"NOT"(CONSTANT L : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    result = L.new()
    result.setVal(unary_op(not_table, L.getVal()))
    return result

def func9(L, R):
    """"OR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    result = L.new()    
    result.setVal([or_table[x][y] for x,y in zip(L.getVal(), R.getVal())])
    return result

def func10(L, R):
    """"XOR"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01"""
    result = StdLogic()    
    result.setVal(binary_op(xor_table, L.getVal(), R.getVal()))
    return result

def func11(L, R):
    """"AND"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01"""
    result = StdLogic()    
    result.setVal(binary_op(and_table, L.getVal(), R.getVal()))
    return result

def func12(L, R):
    """"OR"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01"""
    result = StdLogic()    
    result.setVal(binary_op(or_table, L.getVal(), R.getVal()))
    return result

def func13(L):
    """"NOT"(CONSTANT L : STD_ULOGIC) RETURN UX01"""
    result = StdLogic()    
    result.setVal(unary_op(not_table, L.getVal()))
    return result

def func14(a, b):
    """"&"(CONSTANT A : STD_LOGIC, CONSTANT B : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    return StdLogicVector([str(len(a)), 'DOWNTO', '0']).setVal(b.getVal() + a.getVal())

def func15(a, b):
    """"&"(CONSTANT A : STD_LOGIC, CONSTANT B : STD_LOGIC) RETURN STD_LOGIC_VECTOR"""
    return StdLogicVector(['1', 'DOWNTO', '0']).setVal(b.getVal() + a.getVal())

def func16(L, R):
    """"AND"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    result = L.new()    
    result.setVal([and_table[x][y] for x,y in zip(L.getVal(), R.getVal())])
    return result


def func17(L, R):
    """"NOR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    temp = L.new()    
    temp.setVal([or_table[x][y] for x,y in zip(L.getVal(), R.getVal())])
    
    result = L.new()
    result.setVal(unary_op(not_table, temp.getVal()))
    return result

def func18(L, R):
    """"/="(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN BOOLEAN"""
    return not L.getVal() == R.getVal()

def func19(L, R):
    """"XOR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    result = L.new()    
    result.setVal([xor_table[x][y] for x,y in zip(L.getVal(), R.getVal())])
    return result

def func20(L, R):
    """"-"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR"""
    
    sum = []
    c = 3   # Equivalent to encode('1')         
    result = L.new()
    
    for x, y in zip(R._val, L._val):
        q,c = sub_table[add_table_index[x]][add_table_index[y]][add_table_index[c]]
        sum.append(q)
    
    result._val = sum 
    return result

def func21(L, R):
    """"-"(CONSTANT L : INTEGER, CONSTANT R : INTEGER) RETURN INTEGER"""
    return L - R

def func22(L, R):
    """"+"(CONSTANT L : INTEGER, CONSTANT R : INTEGER) RETURN INTEGER"""
    return L + R

def func23(L, R):
    """">"(CONSTANT L : INTEGER, CONSTANT R : INTEGER) RETURN BOOLEAN"""
    return L > R

def func24(L, R):
    """"="(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN BOOLEAN"""
    return L.getVal() == R.getVal()

def func25(L, R):
    """"/="(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN BOOLEAN"""
    return not L.getVal() == R.getVal()

#------------------------------------------------------------------------------

def registerAll(module):

    mm     = module.__dict__    
    result = {}
    
    for func_name in [name for name in mm.keys() if name.startswith('func')]:
        func = mm[func_name]
        result[func.__doc__] = func
        
    return result

#------------------------------------------------------------------------------

def mapping(module):

    mm = module.__dict__
    
    print '*** std_logic_1164 mapping:'
    
    result = {}
    for func_name in [name for name in mm.keys() if name.startswith('func')]:
        func = mm[func_name]
        argc = func.func_code.co_argcount
        print "  %s : (std_logic_1164.%s %d)" % (func.__doc__, func_name, argc)
        result[func.__doc__] = (func, argc)
        
    print
        
    return result
     