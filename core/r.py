import base64
import ldap

d="sagar Kale"
a=base64.urlsafe_b64encode("".join(d).encode(encoding="utf-8"))
print(a)
b = base64.urlsafe_b64decode(a)
b=str(b,'utf-8')
print(type(b))
print(b)

connection=ldap.initialize("ldap://172.29.21.5:389")
connection.simple_bind_s("GSLAB\gsc-30185", "becalmT217@")
print(connection)

a=[b'GSC-30185']
print(a[0].decode())

a=b'Rahul Mishra'.decode()
print(a)

base64encode