
def bytesToHexString(bs):
    '''
    bytes to hex string 
    eg:
    b'\x01#Eg\x89\xab\xcd\xef\x01#Eg\x89\xab\xcd\xef'
    '01 23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF'
    '''
    # hex_str = ''
    # for item in bs:
    #     hex_str += str(hex(item))[2:].zfill(2).upper() + " "
    # return hex_str
    return ''.join(['%02X ' % b for b in bs])


def hexStringTobytes(str):
    '''
    hex string to bytes
    eg:
    '01 23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF'
    b'\x01#Eg\x89\xab\xcd\xef\x01#Eg\x89\xab\xcd\xef'
    '''
    try:
        str = str.replace(" ", "")
        hex_data = bytes.fromhex(str)
    except:
        return 0
    return hex_data

    # return a2b_hex(str)


def bytesToString(bs):
    '''
    bytes to string
    eg:
    b'0123456789ABCDEF0123456789ABCDEF'
    '0123456789ABCDEF0123456789ABCDEF'
    '''
    return bytes.decode(bs,encoding='utf8')


def stringTobytes(str):
    '''
    string to bytes
    eg:
    '0123456789ABCDEF0123456789ABCDEF'
    b'0123456789ABCDEF0123456789ABCDEF'
    '''
    return bytes(str,encoding='utf8')