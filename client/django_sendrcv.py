#!/usr/bin/python
"""PiConga Client Django Send/Receive Module
   
   This module handles talking to the Django server.
   """
   
# Python imports
import json
import logging
import requests
from uuid import getnode

# External library imports
import requests

# Set up logging for this module. Child of the core client logger.
logger = logging.getLogger("piconga.django")

class ServerError(Exception):
    """Exception raised when the server returns an error."""
    
    def __init__(self, text):
        """Constructor."""
    
        self.value = text
        return
        
    def __str__(self):
        """String representation of this error."""
        return str(self.value)

            
class DjangoSendRcv(object):
    """Object to communicate with the Django server."""
    
    # Private functions
    
    def __init__(self, base_url):
        """Constructor.  Save off the server's base URL."""
        
        self._base_url = base_url
        self._session = requests.Session()
        
        return
        
    
    # Public functions    
   
    def register_user(self, username, password):
        """Register a user with the Django server.  Returns the user's
        User ID for joining Congas."""
        
        logger.debug("Registering user %s", username)
        mac = ':'.join('%02X' %
                     ((getnode() >> 8*i) & 0xff) for i in reversed(xrange(6)))
        payload = {'username': username,
                   'password': password,
                   'mac': mac}
        headers = {'content-type': 'application/json'}
        r = self._session.post(self._base_url + '/user/',
                               data=json.dumps(payload),
                               headers=headers)
        
        if r.status_code != 200:
            raise ServerError, "Registering user %s failed: %s" % (username,
                                                                   r.text)
                                                                   
        # Extract and return the user ID from the returned JSON.
        json_dict = json.loads(r.text)
        
        return int(json_dict["id"])
        
        
    def unregister_user(self, username, password):
        """Unregister a user from the Django server.  Strictly speaking this
        isn't necessary because the server doesn't need you to remove a user
        before re-adding it, but it's a nicely symmetrical API.
        """
        
        logger.debug("Unregistering user %s", username)
        payload = {'username': username, 'password': password}
        headers = {'content-type': 'application/json'}
        r = self._session.delete(self._base_url + '/user/',
                                 data=json.dumps(payload),
                                 headers=headers)
                           
        if r.status_code != 200:
            raise ServerError, "Unregistering user %s failed: %s" % (username,
                                                                     r.text)
            
        return
        
        
    def create_conga(self, name, password):
        """Create a Conga.  Note that the parameters here are not the 
        user's credentials, but those of the Conga to create.
        """
        
        logger.debug("Creating Conga %s", name)
        payload = {'name': name, 'password': password}
        headers = {'content-type': 'application/json'}
        r = self._session.post(self._base_url + '/conga/',
                               data=json.dumps(payload),
                               headers=headers)
                            
        if r.status_code != 200:
            raise ServerError("Creating conga failed: (%d) %s" % 
                              (r.status_code, r.text))
            
        return
        
        
    def join_conga(self, name, password):
        """Join a Conga.  Note that the parameters are those for the conga
        when it was created and not those of the user trying to join the conga.
        """
        
        logger.debug("Joining Conga %s", name)
        payload = {'name': name, 'password': password}
        headers = {'content-type': 'application/json'}
        r = self._session.put(self._base_url + '/conga/',
                              data=json.dumps(payload),
                              headers=headers)
                            
        if r.status_code != 200:
            raise ServerError("Joining conga failed: (%d) %s" % 
                              (r.status_code, r.text))
            
        return
        
        
    def leave_conga(self, name, password):
        """Leave a Conga.  As with join_conga, the name parameter is the name
        of the Conga, but the password is the user's password.
        """
        
        logger.debug("Leaving Conga %s", name)
        headers = {'content-type': 'application/json'}
        r = self._session.delete(self._base_url + '/conga/'+name,
                           headers=headers)
                           
        if r.status_code != 200:
            raise ServerError, "Leaving conga failed: %s" % (r.text)
            
        return
        
