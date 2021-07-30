import requests
from config import config
from threading import Timer, Lock
import certifi
import json
import base64
from functools import wraps
import time

(
    AUTH_HOST,
    REALM,
    CLIENT_ID,
    CLIENT_SECRET,
    REFRESH_GAP,
    USERNAME,
    PASSWORD,
) = (
    config.AUTH_HOST,
    config.REALM,
    config.CLIENT_ID,
    config.CLIENT_SECRET,
    config.REFRESH_GAP,
    config.USERNAME,
    config.PASSWORD,
)


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def may_insist_up_to(times, delay_in_secs=0):
    def wil_retry_if_fails(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            failures = 0
            while failures < times:
                try:
                    return fn(*args, **kwargs)
                except Exception as error:
                    failures += 1
                    if failures > times:
                        raise error
                    else:
                        print("+", end="")
                        time.sleep(delay_in_secs)

        return wrapped

    return wil_retry_if_fails


class OIDC:
    def __init__(
        self,
        username=USERNAME,
        host=AUTH_HOST,
        realm=REALM,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    ):
        self.username = username
        self.host = host
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token_locked = Lock()
        self._last_res = None
        self._refresh_timer = None
        self._when_login_callback = None
        self._when_refresh_callback = None
        self._update_credentials()

    def _update_credentials(
        self,
        access_token=None,
        refresh_token=None,
        expires_in=None,
        refresh_expires_in=None,
        **other,
    ):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_in = expires_in
        self._resfresh_expires_in = refresh_expires_in

    @property
    def access_token(self):
        self._access_token_locked.acquire()
        result = self._access_token
        self._access_token_locked.release()
        return result

    @property
    def access_token_parsed(self):
        _header, payload, _sig = self.access_token.split(".")
        payload = payload + "=" * divmod(len(payload), 4)[1]
        return json.loads(base64.urlsafe_b64decode(payload))

    @property
    def refresh_token(self):
        return self._refresh_token

    @property
    def expires_in(self):
        return self._expires_in

    @property
    def refresh_expires_in(self):
        return self._resfresh_expires_in

    @property
    def url(self):
        path = (
            f"{self.host}/auth/realms/{self.realm}"
            "/protocol/openid-connect/token"
        )
        return path.format(self=self)

    def when_login(self, callback):
        self._when_login_callback = callback

    def when_refresh(self, callback):
        self._when_refresh_callback = callback

    @may_insist_up_to(3, delay_in_secs=1)
    def send_login_request(self, login):
        response = requests.post(
            self.url,
            data=login,
            verify=certifi.where(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code == 401:
            # No need to be blunt
            return None
        response.raise_for_status()
        return response

    def do_login(self, password=PASSWORD, username=None, auto_update=True):
        login = {
            "grant_type": "password",
            "username": self.username if username is None else username,
            "password": password,
            "client_id": self.client_id,
        }
        if self.client_secret is not None:
            login["client_secret"] = self.client_secret
        response = self.send_login_request(login)

        credentials = response.json()
        assert "access_token" in credentials
        if self._when_login_callback is not None:
            self._when_login_callback()
        self._update_credentials(**credentials)
        if auto_update is True:
            self.prepare_refresh()

    def prepare_refresh(self):
        assert self.expires_in is not None

        def perform_refresh():
            self.do_refresh()

        self._refresh_timer = RepeatTimer(
            self.expires_in - REFRESH_GAP, perform_refresh
        )
        self._refresh_timer.start()

    @may_insist_up_to(5, delay_in_secs=1)
    def send_refresh_request(self, refresh):
        response = requests.post(
            self.url,
            data=refresh,
            verify=certifi.where(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response

    def do_refresh(self):
        assert self.refresh_token is not None
        print("Performing token update.", end="")
        self._access_token_locked.acquire()
        refresh = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
        }
        if self.client_secret is not None:
            refresh["client_secret"] = self.client_secret
        try:
            response = self.send_refresh_request(refresh)
            credentials = response.json()
            assert credentials.get("access_token") is not None
            self._update_credentials(**credentials)
            print(" Done.")
        except Exception:
            print(" Failed.")
            return self.do_login()
        finally:
            self._access_token_locked.release()
        if self._when_refresh_callback is not None:
            self._when_refresh_callback()

    def stop(self):
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()
