
from pytk.core.authenticator import Authenticator

from zombie.shotgunengine import ShotgunEngine

class ShotgunAuth(Authenticator):

    def __init__(self, sgEngine=None):
        super(ShotgunAuth, self).__init__()
        self._shotgun = sgEngine if sgEngine else ShotgunEngine()

    def loggedUser(self, *args, **kwargs):
        userData = self._shotgun.getLoggedUser(*args, **kwargs)
        return userData

    def login(self, *args, **kwargs):
        userData = self._shotgun.loginUser(*args, **kwargs)
        return userData

    def logout(self, *args, **kwargs):
        self._shotgun.logoutUser(*args, **kwargs)
