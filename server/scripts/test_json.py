import requests, json
from time import sleep
from uuid import getnode

def add_user(session, username, password):
    mac = ':'.join('%02X' %
        ((getnode() >> 8*i) & 0xff) for i in reversed(xrange(6)))
    payload = {'username': username,
               'password': password,
               'mac': mac}
    headers = {'content-type': 'application/json'}
    r = session.post('http://localhost/conga/user/',
                     data=json.dumps(payload),
                     headers=headers)
    return r

def del_user(session, username, password):
    payload = {'username': username, 'password': password}
    headers = {'content-type': 'application/json'}
    r = session.delete('http://localhost/conga/user/',
                       data=json.dumps(payload),
                       headers=headers)
    return r

def add_conga(session, name, password):
    payload = {'name': name, 'password': password}
    headers = {'content-type': 'application/json'}
    r = session.post('http://localhost/conga/conga/',
                     data=json.dumps(payload),
                     headers=headers)
    return r

def join_conga(session, name, password):
    payload = {'name': name, 'password': password}
    headers = {'content-type': 'application/json'}
    r = session.put('http://localhost/conga/conga/',
                    data=json.dumps(payload),
                    headers=headers)
    return r

def del_conga(session, name, password):
    headers = {'content-type': 'application/json'}
    r = session.delete('http://localhost/conga/conga/'+name,
                       headers=headers)
    return r

# Create sessions for this test
s1 = requests.Session()
s2 = requests.Session()
s3 = requests.Session()
s4 = requests.Session()

# Check a rubbish request
print "\nRubbish request"
r = s1.get('http://localhost/conga/user/')
print r.status_code, r.text, r.elapsed

# Create the user on first registration
print "\nRegister"
r = add_user(s1, "peter", "secret")
print r.status_code, r.text, r.elapsed
r = add_user(s2, "paul", "another_secret")
print r.status_code, r.text, r.elapsed
r = add_user(s3, "jane", "more_secrets")
print r.status_code, r.text, r.elapsed
r = add_user(s4, "john", "whatever")
print r.status_code, r.text, r.elapsed

# Allow re-regsitration
print "\nRe-register"
r = add_user(s1, "peter", "secret")
print r.status_code, r.text, r.elapsed

# Get the user details
print "\nRead user"
r = s1.get('http://localhost/conga/user/peter')
print r.status_code, r.text, r.elapsed

# Get another user details - should fail?
r = s2.get('http://localhost/conga/user/peter')
print r.status_code, r.text, r.elapsed

# Check overwrite does not work.
print "\nClaim user - should not be allowed"
r = add_user(s1, "peter", "secret2")
print r.status_code, r.text, r.elapsed

# Create a conga
print "\nCreate conga"
r = add_conga(s1, "conga1", "conga1pw")
print r.status_code, r.text, r.elapsed
r = add_conga(s3, "conga2", "conga2pw")
print r.status_code, r.text, r.elapsed

# Join the conga
print "\nJoin conga"
r = join_conga(s2, "conga1", "conga1pw")
print r.status_code, r.text, r.elapsed
r = join_conga(s4, "conga2", "bad_password")
print r.status_code, r.text, r.elapsed
r = join_conga(s4, "conga1", "conga1pw")
print r.status_code, r.text, r.elapsed

# Get the conga details
print "\nRead conga"
r = s1.get('http://localhost/conga/conga/New%20conga')
print r.status_code, r.text, r.elapsed
r = s1.get('http://localhost/conga/conga/conga2')
print r.status_code, r.text, r.elapsed
r = s1.get('http://localhost/conga/conga/conga1')
print r.status_code, r.text, r.elapsed

print "\nPause...."
sleep(1)

# Delete the conga
print "\nDelete conga"
r = del_conga(s1, "conga1", "conga1pw")
print r.status_code, r.text, r.elapsed

print "\nPause...."
sleep(1)

r = del_conga(s3, "conga2", "conga2pw")
print r.status_code, r.text, r.elapsed

# Delete the user
print "\nDeregister"
r = del_user(s1, "peter", "bad_password")
print r.status_code, r.text, r.elapsed
r = del_user(s1, "peter", "secret")
print r.status_code, r.text, r.elapsed
r = del_user(s2, "paul", "another_secret")
print r.status_code, r.text, r.elapsed
r = del_user(s3, "jane", "more_secrets")
print r.status_code, r.text, r.elapsed
r = del_user(s4, "john", "whatever")
print r.status_code, r.text, r.elapsed
