import requests, json

# Create a session for this test
s = requests.Session()

# Check a rubbish request
print "\nRubbish request"
r = s.get('http://localhost:8000/conga/user/')
print r.status_code, r.text

payload = {'username': 'peter', 'password': 'secret'}
headers = {'content-type': 'application/json'}

# Create the user on first registration
print "\nRegister"
r = s.post('http://localhost:8000/conga/user/',
           data=json.dumps(payload),
           headers=headers)
print r.status_code, r.text

# Allow re-regsitration
print "\nRe-register"
r = s.post('http://localhost:8000/conga/user/',
           data=json.dumps(payload),
           headers=headers)
print r.status_code, r.text

# Get the user details
print "\nRead user"
r = s.get('http://localhost:8000/conga/user/peter')
print r.status_code, r.text

# Check overwrite does not work.
print "\nClaim user - should not be allowed"
payload = {'username': 'peter', 'password': 'secret2'}
r = s.post('http://localhost:8000/conga/user/',
           data=json.dumps(payload),
           headers=headers)
print r.status_code, r.text

# Delete the user
print "\nDeregister"
payload = {'username': 'peter', 'password': 'secret'}
r = s.delete('http://localhost:8000/conga/user/',
             data=json.dumps(payload),
             headers=headers)
print r.status_code, r.text
