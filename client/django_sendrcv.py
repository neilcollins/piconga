#!/usr/bin/python
"""PiConga Client Django Send/Receive Module
   
   This module handles talking to the Django server.
   """
   
# Python imports
import json
from uuid import getnode

# External library imports
import requests

class DjangoSendRcv(object):
    """Object to communicate with the Django server."""
    
    class ServerError(Exception):
        """Exception raised when the server returns an error."""
        
        def __init__(self):
        """Constructor."""
        
        self.value = "Lost connection with the Tornado server."
        return
            
            
        def __str__(self):
            """String representation of this error."""
            return repr(self.value)
            
            
    # Private functions
    
    def __init__(self, base_url):
        """Constructor.  Save off the server's base URL."""
        
        self._base_url = base_url
        
        return
        
    
    # Public functions    
   
    def register_user(self, username, password):
        """Register a user with the Django server.  Returns the user's
        User ID for joining Congas."""
        
        mac = ':'.join('%02X' %
                     ((getnode() >> 8*i) & 0xff) for i in reversed(xrange(6)))
        payload = {'username': username,
                   'password': password,
                   'mac': mac}
        headers = {'content-type': 'application/json'}
        r = session.post(self._base_url + '/user/',
                         data=json.dumps(payload),
                         headers=headers)
        
        if r.status_code != 200:
            raise ServerError, "Registering user %s failed: %s" % (username,
                                                                   r.text)
                                                                   
        # Extract and return the user ID from the returned JSON.
        json_dict = json.load(r.text)
        
        return int(json_dict["id"])
        
        
    def unregister_user(self, username, password):
        """Unregister a user from the Django server.  Strictly speaking this
        isn't necessary because the server doesn't need you to remove a user
        before re-adding it, but it's a nicely symmetrical API.
        """
        
        payload = {'username': username, 'password': password}
        headers = {'content-type': 'application/json'}
        r = session.delete(self._base_url + '/user/',
                           data=json.dumps(payload),
                           headers=headers)
                           
        if r.status_code != 200:
            raise ServerError, "Unregistering user %s failed: %s" % (username,
                                                                     r.text)
            
        return
        
        
    def join_conga(self, name, password):
        """Join a Conga.  Note that the name parameter here is not the 
        user's username, but the name of the Conga to create.  The password,
        however, is the user's password.
        """
        
        payload = {'name': name, 'password': password}
        headers = {'content-type': 'application/json'}
        r = session.put(self._base_url + '/conga/',
                        data=json.dumps(payload),
                        headers=headers)
                            
        if r.status_code != 200:
            raise ServerError, "Joining conga failed: %s" % (r.text)
            
        return
        
        
    def leave_conga(self, name, password):
        """Leave a Conga.  As with join_conga, the name parameter is the name
        of the Conga, but the password is the user's password.
        """
        
        headers = {'content-type': 'application/json'}
        r = session.delete(self._base_url + '/conga/'+name,
                           headers=headers)
                           
        if r.status_code != 200:
            raise ServerError, "Leaving conga failed: %s" % (r.text)
            
        return
        