k1      = bytes.fromhex("3c3f0193af37d2ebbc50cc6b91d27cf61197")
k21     = bytes.fromhex("ff76edcad455b6881b92f726987cbf30c68c")
k23     = bytes.fromhex("611568312c102d4d921f26199d39fe973118")
k1234   = bytes.fromhex("91ec5a6fa8a12f908f161850c591459c3887")
f45     = bytes.fromhex("0269dd12fe3435ea63f63aef17f8362cdba8")

bxor = lambda a, b: bytes(x ^ y for x, y in zip(a, b))

k2 = bxor(k1, k21)        
k3 = bxor(k2, k23)        
k4 = bxor(k1234, bxor(bxor(k1, k2), k3)) 

k5flag = bxor(f45, k4)

known_prefix = b"cry{"

key5 = bxor(k5flag[:4], known_prefix)

flag = bytes(k5flag[i] ^ key5[i % 4] for i in range(len(k5flag)))

print(flag.decode())