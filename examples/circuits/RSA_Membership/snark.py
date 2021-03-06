PAIRING_MODULUS = 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001
INT_WIDTH = 64
INT_HEX_WIDTH = INT_WIDTH/4

# Note that gen_xxx is a test function to create input variables

def group1(x):
    return x % PAIRING_MODULUS

def group1hex(x):
    return format(group1(x),'x')

def hex(x):
    return format(group1(x),'x')

def str(x):
    return format(group1(x),'d')

def array(x):
    return "["+format(group1(x),'d')+"]"

def ifelse(cond_name, true_name, false_name, out_name, size):
    arith_code = ""
    for i in range(size):
        arith_code += "const-mul-neg-1 in 1 <" +true_name+ "["+str(i)+"]> out 1 <"+ true_name+".neg["+str(i)+"]>\n"
        arith_code += "const-mul-neg-1 in 1 <" +false_name+ "["+str(i)+"]> out 1 <"+ false_name+".neg["+str(i)+"]>\n"
        arith_code += "add in 2 <"+true_name +"["+str(i)+"] "+false_name+".neg["+str(i)+"]> out 1 <"+out_name+".rvalue["+str(i)+"]>\n"
        arith_code += "add in 3 <"+out_name + "["+str(i)+"] "+true_name +".neg["+str(i)+" "+false_name+".neg["+str(i)+"]> out 1 <"+out_name+".lvalue["+str(i)+"]>\n"
        arith_code += "mul in 2 <"+cond_name+" "+out_name+".rvalue["+str(i)+"]> out 1<"+out_name+".lvalue["+str(i)+"]>\n"

    return arith_code

def gen_input(x_name, x, x_size):
    x_hex = format(x,'x')
    x_len = len(x_hex)
    arith_code = ""
    input_code = ""
    for i in range(x_size):
        arith_code += "input "+x_name+array(i)+"\n"
        input_code += x_name+array(i)+" "+ get_number(x_hex, x_len, i) +"\n"

    return arith_code, input_code

def gen_sqr(x_name, z_name, x, x_size):
    arith_code, input_code = gen_input(x_name, x, x_size)
    arith_code2, input_code2 = sqr(x_name, z_name, x, x_size)

    return arith_code+arith_code2, input_code+input_code2

def get_number(x_hex, x_len, i):
    if x_len<=INT_HEX_WIDTH*i:
        return "0"
    elif x_len<=INT_HEX_WIDTH*(i+1):
        return "0"+x_hex[:x_len - INT_HEX_WIDTH*i]
    else:
        return "0"+x_hex[x_len - INT_HEX_WIDTH*(i+1):x_len - INT_HEX_WIDTH*i]

def prepare_sqr(x_name, z_name, x, x_size):
    z = x*x;
    z_hex = format(z,'x')
    z_len = len(z_hex)
    x_hex = format(x,'x')
    x_len = len(x_hex)
    arith_code = ""
    input_code = ""

    sqr_name = x_name+".sqr"
    const_name = x_name+"_const"
    sum_name = x_name+"_sum"
    sqr_const_name = x_name+".sqr_const"
    sqr_sum_name = x_name+".sqr_sum"
    remain_name = z_name+".remain"

    # create intermediate z[] values using convolution
    z_size = 2*x_size-1;            
    zw = []
    for i in range(z_size):
        sum = 0
        for j in range(x_size):
            k = i-j
            if k<0:
                break
            sum += int(get_number(x_hex, x_len, j), 16) * int(get_number(x_hex, x_len, k), 16)
        zw.append(sum)

    for i in range(z_size):
        arith_code += "nizkinput "+z_name+"["+str(i)+"]\n"
        input_code += z_name+"["+str(i)+"] "+ get_number(z_hex, z_len, i) +"\n"

    for i in range(z_size):
        arith_code += "nizkinput "+sqr_name+array(i)+"\n"
        input_code += sqr_name+array(i)+" 0"+ hex(zw[i]) +"\n"

    rm = []
    remain = hex(int(hex(zw[0]),16) - int(get_number(z_hex, z_len, 0),16))
    rm.append(int(get_number(remain, len(remain), 1),16))
    for i in range(1,z_size-1):
        remain = hex(int(hex(zw[i]),16) - int(get_number(z_hex, z_len, i),16) + rm[i-1])
        rm.append(int(get_number(remain, len(remain), 1),16))

    for i in range(0,z_size-1):
        arith_code += "nizkinput "+remain_name+array(i)+"\n"
        input_code += remain_name+array(i)+" 0"+ hex(rm[i]) +"\n"

    return arith_code, input_code, zw

def sqr(x_name, z_name, x, x_size):
    sqr_name = x_name+".sqr"
    z_size = 2*x_size-1;            

    arith_code, input_code,zw = prepare_sqr(x_name, z_name, x, x_size)
    arith_code += sqr_internal(x_name, sqr_name, zw, x_size, z_size)
    arith_code += eq_long_integer(sqr_name, z_name, z_size)

    return arith_code, input_code


def sqr_internal(x_name, sqr_name, zw, x_size, z_size):
    arith_code = ""

    const_name = x_name+"_const"
    sum_name = x_name+"_sum"
    sqr_const_name = sqr_name+"_const"
    sqr_sum_name = sqr_name+"_sum"

    for i in range(1,z_size+1):
        arith_code += "#Case : s == " +str(i)+"\n"
        for j in range(x_size):
            arith_code += "const-mul-"+group1hex(pow(i,j)) + " in 1 <"+x_name+array(j)+"> out 1 <"+const_name+array(i)+array(j)+">\n"
        arith_code += "add in "+str(x_size) + " <"
        for j in range(x_size):
            arith_code += const_name+array(i)+array(j)+" "
        arith_code += "> out 1 <"+sum_name+array(i)+">\n"   
        for j in range(z_size):
            arith_code += "const-mul-"+group1hex(pow(i,j)) + " in 1 <"+sqr_name+array(j)+"> out 1 <"+sqr_const_name+array(i)+array(j)+">\n"
        arith_code += "add in "+str(z_size) + " <"
        for j in range(z_size):
            arith_code += sqr_const_name+array(i)+array(j)+" "
        arith_code += "> out 1 <"+sqr_sum_name+array(i)+">\n"   

        arith_code += "assert in 2 <"+sum_name+array(i)+" "+sum_name+array(i)+"> out 1 <"+sqr_sum_name+array(i)+">\n"

    return arith_code

def eq_long_integer(sqr_name, z_name, z_size):
    arith_code = ""
    # constraint for sqr, z, remain
    # sqr[0] == z[0]+r[0]*2^64
    # sqr[1]+r[0] == z[1]+r[1]*2^64
    # sqr[2]+r[1] == z[2]+r[2]*2^64
    # ...
    # sqr[32]+r[31] == z[32]

    remain_name = z_name+".remain"
    remain_const_name = z_name+".remain_const"
    right_name = z_name+"_sum_remain"
    for i in range(z_size-1):
        arith_code += "const-mul-"+group1hex(pow(2,INT_WIDTH)) + " in 1 <"+remain_name+array(i)+"> out 1 <"+remain_const_name+array(i)+">\n"
        arith_code += "add in 2 <"+z_name+array(i)+" "+remain_const_name+array(i)+"> out 1 <"+right_name+array(i)+">\n"

    left_name = z_name+"_sum_mul"
    for i in range(1,z_size):
        arith_code += "add in 2 <"+sqr_name+array(i)+" "+remain_const_name+array(i-1)+"> out 1 <"+left_name+array(i)+">\n"

    arith_code += "assert in 2 <"+sqr_name+array(0)+" one> out 1 <"+ right_name+array(0)+">\n"
    for i in range(1,z_size-1):
        arith_code += "assert in 2 <"+left_name+array(i)+" one> out 1 <"+ right_name+array(i)+">\n"

    arith_code += "assert in 2 <"+left_name+array(z_size-1)+" one> out 1 <"+ z_name+array(z_size-1)+">\n"
     
    return arith_code
            

def gen_mul(x_name, y_name, z_name, x, y, x_size, y_size):
    arith_code, input_code = gen_input(x_name, x, x_size)
    arith_code2, input_code2 = gen_input(y_name, y, y_size)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = mul(x_name, y_name, z_name, x, y, x_size, y_size)
    arith_code += arith_code2
    input_code += input_code2

    return arith_code, input_code

def prepare_mul(x_name, y_name, z_name, x, y, x_size, y_size):
    z = x*y;
    z_hex = format(z,'x')
    z_len = len(z_hex)
    x_hex = format(x,'x')
    x_len = len(x_hex)
    y_hex = format(y,'x')
    y_len = len(y_hex)
    arith_code = ""
    input_code = ""

    mul_name = z_name+".mul"
    const_name = z_name+"_const"
    sum_name = z_name+"_sum"
    mul_const_name = z_name+".mul_const"
    mul_sum_name = z_name+".mul_sum"
    remain_name = z_name+".remain"

    # create intermediate z[] values using convolution
    z_size = x_size+y_size-1;            
    zw = []
    for i in range(z_size):
        sum = 0
        for j in range(x_size):
            k = i-j
            if k<0:
                break
            sum += int(get_number(x_hex, x_len, j), 16) * int(get_number(y_hex, y_len, k), 16)
        zw.append(sum)

    for i in range(z_size):
        arith_code += "nizkinput "+z_name+"["+str(i)+"]\n"
        input_code += z_name+"["+str(i)+"] "+ get_number(z_hex, z_len, i) +"\n"

    for i in range(z_size):
        arith_code += "nizkinput "+mul_name+array(i)+"\n"
        input_code += mul_name+array(i)+" 0"+ hex(zw[i]) +"\n"

    rm = []
    remain = hex(int(hex(zw[0]),16) - int(get_number(z_hex, z_len, 0),16))
    rm.append(int(get_number(remain, len(remain), 1),16))
    for i in range(1,z_size-1):
        remain = hex(int(hex(zw[i]),16) - int(get_number(z_hex, z_len, i),16) + rm[i-1])
        rm.append(int(get_number(remain, len(remain), 1),16))

    for i in range(0,z_size-1):
        arith_code += "nizkinput "+remain_name+array(i)+"\n"
        input_code += remain_name+array(i)+" 0"+ hex(rm[i]) +"\n"

    return arith_code, input_code, zw

def mul(x_name, y_name, z_name, x, y, x_size, y_size):
    mul_name = z_name+".mul"
    z_size = x_size+y_size-1;            

    arith_code, input_code,zw = prepare_mul(x_name, y_name, z_name, x, y, x_size, y_size)
    arith_code += mul_internal(x_name, y_name, mul_name, x_size, z_size)
    arith_code += eq_long_integer(mul_name, z_name, z_size)

    return arith_code, input_code

def mul_internal(x_name, y_name, z_name, x_size, y_size):
    arith_code = ""
    z_size = x_size+y_size-1;            

    for i in range(1,z_size+1):
        arith_code += "#Case : s == " +str(i)+"\n"
        for j in range(x_size):
            arith_code += "const-mul-"+group1hex(pow(i,j)) + " in 1 <"+x_name+"["+str(j)+"]> out 1 <"+x_name+"_const["+str(i)+"]["+str(j)+"]>\n"
        arith_code += "add in "+str(x_size) + " <"
        for j in range(x_size):
            arith_code += x_name+"_const["+str(i)+"]["+str(j)+"] "
        arith_code += "> out 1 <"+x_name+"_sum["+str(i)+"]>\n"   
        for j in range(y_size):
            arith_code += "const-mul-"+group1hex(pow(i,j)) + " in 1 <"+y_name+"["+str(j)+"]> out 1 <"+y_name+"_const["+str(i)+"]["+str(j)+"]>\n"
        arith_code += "add in "+str(y_size) + " <"
        for j in range(y_size):
            arith_code += y_name+"_const["+str(i)+"]["+str(j)+"] "
        arith_code += "> out 1 <"+y_name+"_sum["+str(i)+"]>\n"   
        for j in range(z_size):
            arith_code += "const-mul-"+group1hex(pow(i,j)) + " in 1 <"+z_name+"["+str(j)+"]> out 1 <"+z_name+"_const["+str(i)+"]["+str(j)+"]>\n"
        arith_code += "add in "+str(z_size) + " <"
        for j in range(z_size):
            arith_code += z_name+"_const["+str(i)+"]["+str(j)+"] "
        arith_code += "> out 1 <"+z_name+"_sum["+str(i)+"]>\n"   
        
        arith_code += "assert in 2 <"+x_name+"_sum["+str(i)+"] "+y_name+"_sum["+str(i)+"]> out 1 <"+z_name+"_sum["+str(i)+"]>\n"

    return arith_code

def gen_sqr_mod_n(x_name, z_name, n_name, name, x, n, x_size, n_size):
    arith_code, input_code = gen_input(x_name, x, x_size)
    arith_code2, input_code2 = gen_input(n_name, n, n_size)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = sqr_mod_n(x_name, z_name, n_name, name, x, n, x_size, n_size)
    arith_code += arith_code2
    input_code += input_code2

    return arith_code, input_code

def sqr_mod_n(x_name, z_name, n_name, name, x, n, x_size, n_size):
    temp_name = name +"_temp"
    arith_code, input_code = sqr(x_name, temp_name, x, x_size)
    sub_temp_name = temp_name +"_sub"

    z = x*x % n
    z_size = 2*x_size-1;            
    z_hex = format(z,'x')
    z_len = len(z_hex)
    for i in range(z_size):
        arith_code += "nizkinput "+z_name+"["+str(i)+"]\n"
        input_code += z_name+"["+str(i)+"] "+ get_number(z_hex, z_len, i) +"\n"
    for i in range(z_size):
        arith_code += "add in 2 <"+z_name+"["+str(i)+"] "+sub_temp_name+"["+str(i)+"]> out 1 <"+temp_name+"["+str(i)+"]>\n"

    q_size = 2*x_size-1 - n_size
    q = x*x / n
    q_hex = format(q,'x')
    q_len = len(q_hex)
    q_name = name+"_q"
    for i in range(q_size):
        arith_code += "nizkinput "+q_name+"["+str(i)+"]\n"
        input_code += q_name+"["+str(i)+"] 0"+ get_number(q_hex, q_len, i) +"\n"
    arith_code2, input_code2 = mul(n_name, q_name, sub_temp_name, n, q, n_size, q_size)
    
    return arith_code+arith_code2, input_code+input_code2
    

def gen_mul_mod_n(x_name, y_name, z_name, n_name, name, x, y, n, x_size, y_size, n_size):
    arith_code, input_code = gen_input(x_name, x, x_size)

    arith_code2, input_code2 = gen_input(y_name, y, y_size)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = gen_input(n_name, n, n_size)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = mul_mod_n(x_name, y_name, z_name, n_name, name, x, y, n, x_size, y_size, n_size)
    arith_code += arith_code2
    input_code += input_code2

    return arith_code, input_code

def mul_mod_n(x_name, y_name, z_name, n_name, name, x, y, n, x_size, y_size, n_size):
    temp_name = name +"_temp"
    arith_code, input_code = mul(x_name, y_name, temp_name, x, y, x_size, y_size)
    sub_temp_name = temp_name +"_sub"

    z = x*y % n
    z_size = x_size+y_size-1;            
    z_hex = format(z,'x')
    z_len = len(z_hex)
    for i in range(z_size):
        arith_code += "nizkinput "+z_name+"["+str(i)+"]\n"
        arith_code += "add in 2 <"+z_name+"["+str(i)+"] "+sub_temp_name+"["+str(i)+"]> out 1 <"+temp_name+"["+str(i)+"]>\n"
        input_code += z_name+"["+str(i)+"] "+ get_number(z_hex, z_len, i) +"\n"

    q_size = x_size+y_size-1 - n_size
    q = x*y / n
    q_hex = format(q,'x')
    q_len = len(q_hex)
    q_name = name+"_q"
    for i in range(q_size):
        arith_code += "nizkinput "+q_name+"["+str(i)+"]\n"
        input_code += q_name+"["+str(i)+"] 0"+ get_number(q_hex, q_len, i) +"\n"
    arith_code2, input_code2 = mul(n_name, q_name, sub_temp_name, n, q, n_size, q_size)
    
    return arith_code+arith_code2, input_code+input_code2

def gen_exp_mod_n(g_name, e_name, n_name, y_name, name, g, e, n, g_size, e_bits, n_size):
    arith_code, input_code = gen_input(g_name, g, g_size)

    arith_code2, input_code2 = gen_input(e_name, e, e_bits)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = gen_input(n_name, n, n_size)
    arith_code += arith_code2
    input_code += input_code2

    arith_code2, input_code2 = exp_mod_n(g_name, e_name, n_name, y_name, name, g, e, n, g_size, e_bits, n_size)
    arith_code += arith_code2
    input_code += input_code2

    return arith_code, input_code

def exp_mod_n(g_name, e_name, n_name, y_name, name, g, e, n, g_size, e_bits, n_size):
    y = pow(g, e, n)

    arith_code = ""
    input_code = ""

    y_hex = format(y,'x')
    y_len = len(y_hex)
    for i in range(n_size):
        arith_code += "nizkinput "+y_name+"["+str(i)+"]\n"
        input_code += y_name+"["+str(i)+"] "+ get_number(y_hex, y_len, i) +"\n"


    if e_bits<=2:
        arith_code2, input_code2 = sqr_mod_n(g_name, y_name, n_name, name+"[0]", g, n, g_size, n_size)  
    else:
        arith_code2, input_code2 = sqr_mod_n(g_name, name+".table[1]", n_name, name+"[0]", g, n, g_size, n_size)  
    arith_code += arith_code2
    input_code += input_code2
    temp = g
    for i in range(1,e_bits-1):
        temp = temp*temp % n
        arith_code2, input_code2 = sqr_mod_n(name+".table["+str(i)+"]", name+".table["+str(i+1)+"]", n_name, name+"["+str(i)+"]", temp, n, g_size, n_size)  
        arith_code += arith_code2
        input_code += input_code2

    print("table construction is completed\n")

    e_bin = format(e,'b')
    e_len = len(e_bin)
    if int("0"+e_bin[e_len-1:e_len], 2):
        temp_value = g
    else:
        temp_value = 1
    temp = g
    arith_code2, input_code2 = mul_mod_n(name+"_temp_value[0]", name+".table[0]", name+"_true_temp_value[0]", n_name, name+"[0]", temp_value, temp, n, n_size, n_size, n_size) 
    arith_code += arith_code2
    input_code += input_code2
    arith_code += ifelse(e_name+"[0]",name+"_true_temp_value[0]", name+"_temp_value[0]", name+"_temp_value[1]", n_size) 
    for i in range(1,e_bits-1):
        temp = temp*temp %n
        if int("0"+e_bin[e_len-i-1:e_len-i], 2):
                temp_value *= temp
                
        arith_code2,input_code2 = mul_mod_n(name+"_temp_value["+str(i)+"]", name+".table["+str(i)+"]", name+"_true_temp_value["+str(i)+"]", n_name, name+"["+str(i)+"]", temp_value, temp, n, n_size, n_size, n_size) 
        arith_code += arith_code2
        input_code += input_code2
        arith_code += ifelse(e_name+"["+str(i)+"]",name+"_true_temp_value["+str(i)+"]", name+"_temp_value["+str(i)+"]", name+"_temp_value["+str(i+1)+"]", n_size) 

    temp = temp*temp %n
    if int("0"+e_bin[e_len-e_bits:e_len-e_bits+1], 2):
            temp_value *= temp
            
    arith_code2, input_code2 = mul_mod_n(name+"_temp_value["+str(e_bits-1)+"]", name+".table["+str(e_bits-1)+"]", name+"_true_temp_value["+str(e_bits-1)+"]", n_name, name+"["+str(e_bits-1)+"]", temp_value, temp, n, n_size, n_size, n_size) 
    arith_code += arith_code2
    input_code += input_code2
    arith_code += ifelse(e_name+"["+str(e_bits-1)+"]",name+"_true_temp_value["+str(e_bits-1)+"]", name+"_temp_value["+str(e_bits-1)+"]", y_name, n_size) 

    return arith_code, input_code

def convolution_1D(x_name, y_name, z_name, x_size, y_size):
        arith_code = ""
        for i in range(x_size):
            arith_code += "input "+x_name+"["+str(i)+"]\n"
        for i in range(y_size):
            arith_code += "input "+y_name+"["+str(i)+"]\n"
        z_size = x_size+y_size-1;            
        for i in range(z_size):
            arith_code += "nizkinput "+z_name+"["+str(i)+"]\n"

        for i in range(1,z_size+1):
        #for i in range(1,2):
            arith_code += "#Case : s == " +str(i)+"\n"
            for j in range(x_size):
                arith_code += "const-mul-"+format(group1(pow(i,j)),'x') + " in 1 <"+x_name+"["+str(j)+"]> out 1 <"+x_name+"_const["+str(i)+"]["+str(j)+"]>\n"
            arith_code += "add in "+str(x_size) + " <"
            for j in range(x_size):
                arith_code += x_name+"_const["+str(i)+"]["+str(j)+"] "
            arith_code += "> out 1 <"+x_name+"_sum["+str(i)+"]>\n"   
            for j in range(y_size):
                arith_code += "const-mul-"+format(group1(pow(i,y_size-j-1)),'x') + " in 1 <"+y_name+"["+str(j)+"]> out 1 <"+y_name+"_const["+str(i)+"]["+str(j)+"]>\n"
            arith_code += "add in "+str(y_size) + " <"
            for j in range(y_size):
                arith_code += y_name+"_const["+str(i)+"]["+str(j)+"] "
            arith_code += "> out 1 <"+y_name+"_sum["+str(i)+"]>\n"   
            for j in range(z_size):
                arith_code += "const-mul-"+format(group1(pow(i,j)),'x') + " in 1 <"+z_name+"["+str(j)+"]> out 1 <"+z_name+"_const["+str(i)+"]["+str(j)+"]>\n"
            arith_code += "add in "+str(z_size) + " <"
            for j in range(z_size):
                arith_code += z_name+"_const["+str(i)+"]["+str(j)+"] "
            arith_code += "> out 1 <"+z_name+"_sum["+str(i)+"]>\n"   
            
            arith_code += "assert in 2 <"+x_name+"_sum["+str(i)+"] "+y_name+"_sum["+str(i)+"]> out 1 <"+z_name+"_sum["+str(i)+"]>\n"

            print arith_code
            arith_code = ""

        return arith_code


#arith_code, input_code = mul("x","y","z",32,32,2,3)
#arith_code, input_code = mul_mod_n("x","y","z","q", "n", 32,32,32, 8,7,55)
#arith_code, input_code = sqr_mod_n("x","z","q", "n", 32,32, 8,55)
#arith_code, input_code = exp_mod_n("g","y","n",  4, 32, 8, 2, 55)
#arith_code, input_code = gen_sqr("x", "z", 4, 2)
arith_code, input_code = gen_mul("x", "y", "z", 3, 7, 2, 2)
#arith_code, input_code = gen_sqr_mod_n("x", "z", "n", "this", 3, 7, 5, 5)
#arith_code, input_code = gen_mul_mod_n("x", "y", "z", "n", "this", 8, 7, 5, 5, 5, 5)
#arith_code, input_code = gen_exp_mod_n("g","e","n","y", "this", 2, 4, 113, 3, 4, 3)
#arith_code, input_code = gen_exp_mod_n("g","e","n","y", "this", 2, 4, 113, 32, 256, 32)

arith_code = "input 0\n" + "nizkinput one\nconst-mul-0 in 1 <0> out 1 <1>\n"+arith_code
input_code = "0 1\none 1\n"+input_code

arith_file = open("test1.arith", 'w')
arith_file.write(arith_code)
arith_file.close()

input_file = open("test1.in", 'w')
input_file.write(input_code)
input_file.close()

#print(arith_code)
#print(input_code)
#print(convolution_1D("x","y","z",30*30,3*3))

