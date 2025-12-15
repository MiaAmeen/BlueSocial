from time import sleep, time
from typing import Any
from loguru import logger
from dateutil import parser as date_parse
from datetime import datetime, timezone
from curl_cffi import requests
import json
import logging
import os
from dotenv import load_dotenv
from random import expovariate

load_dotenv()

logging.basicConfig(
    level=(
        logging.DEBUG
        if os.getenv("DEBUG") and os.getenv("DEBUG").lower() != "false"
        else logging.INFO
    )
)

BASE_URL = "https://truthsocial.com"
API_BASE_URL = "https://truthsocial.com/api"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"
)

# Oauth client credentials, from https://truthsocial.com/packs/js/application-d77ef3e9148ad1d0624c.js
CLIENT_ID = "9X1Fdd-pxNsAgEDNi_SfhJWi8T-vLuV2WVzKIbkTCw4"
CLIENT_SECRET = "ozF8jzI4968oTKFkEnsBC-UbLPCdrSv0MkXGQu2o_-M"

proxies = {"http": os.getenv("http_proxy"), "https": os.getenv("https_proxy")}

TRUTHSOCIAL_USERNAME = os.getenv("TRUTHSOCIAL_USERNAME")
TRUTHSOCIAL_PASSWORD = os.getenv("TRUTHSOCIAL_PASSWORD")
TRUTHSOCIAL_TOKEN = os.getenv("TRUTHSOCIAL_TOKEN")


class LoginErrorException(Exception):
    pass


class Api:
    def __init__(
        self,
        username=TRUTHSOCIAL_USERNAME,
        password=TRUTHSOCIAL_PASSWORD,
        token=TRUTHSOCIAL_TOKEN,
        silent=False
    ):
        self.ratelimit_max = 300
        self.ratelimit_remaining = None
        self.ratelimit_reset = None
        self.__username = username
        self.__password = password
        self.auth_id = token
        self.sesh = requests.Session(impersonate="chrome")
        self.last_call_time = time() - 1
        self.silent = silent

        if silent:
            logging.disable(logging.CRITICAL)
            logger.remove()

    def __check_login(self):
        """Runs before any login-walled function to check for login credentials and generates an auth ID token"""
        if self.auth_id is None:
            if self.__username is None:
                raise LoginErrorException("Username is missing.")
            if self.__password is None:
                raise LoginErrorException("Password is missing.")
            self.auth_id = self.get_auth_id(self.__username, self.__password)
            logger.warning(f"Using token {self.auth_id}")


    def _check_ratelimit(self, resp):
        if resp.headers.get("x-ratelimit-limit") is not None:
            self.ratelimit_max = int(resp.headers.get("x-ratelimit-limit"))
        if resp.headers.get("x-ratelimit-remaining") is not None:
            self.ratelimit_remaining = int(resp.headers.get("x-ratelimit-remaining"))
        if resp.headers.get("x-ratelimit-reset") is not None:
            self.ratelimit_reset = date_parse.parse(
                resp.headers.get("x-ratelimit-reset")
            )

        if (
            self.ratelimit_remaining is not None and self.ratelimit_remaining <= 50
        ):  # We do 50 to be safe; their tracking is a bit stochastic... it can jump down quickly
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            time_to_sleep = (
                self.ratelimit_reset.replace(tzinfo=timezone.utc) - now
            ).total_seconds()
            logger.warning(
                f"Approaching rate limit; sleeping for {time_to_sleep} seconds..."
            )
            if time_to_sleep > 0:
                sleep(time_to_sleep)
            else:
                sleep(10)

    def _get(self, url: str, params: dict = None) -> Any:
        try:
            wait_time = self.last_call_time + 60 - time()
            if wait_time > 0:
                sleep(wait_time + expovariate(1/60))

            resp = self.sesh.get(
                url=API_BASE_URL + url,
                params=params,
                proxies=proxies,
                impersonate="chrome123",
                headers={
                    "Authorization": "Bearer " + str(self.auth_id),
                    "User-Agent": USER_AGENT,
                },
            )
            self.last_call_time = time()

        except Exception as e:
            logger.error(f"Session error: {e}")
            pass

        # Will also sleep
        self._check_ratelimit(resp)

        try:
            r = resp.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON: {resp.text}")
            r = None

        return r

    def _get_paginated(self, url: str, params: dict = None, resume: str = None) -> Any:
        next_link = API_BASE_URL + url

        if resume is not None:
            next_link += f"?max_id={resume}"

        while next_link is not None:
            wait_time = self.last_call_time + 60 - time()
            if wait_time > 0:
                sleep(wait_time + expovariate(1/60))

            resp = self.sesh.get(
                next_link,
                params=params,
                proxies=proxies,
                impersonate="chrome123",
                headers={
                    "Authorization": "Bearer " + str(self.auth_id),
                    "User-Agent": USER_AGENT,
                },
            )
            self.last_call_time = time()

            link_header = resp.headers.get("Link", "")
            next_link = None
            for link in link_header.split(","):
                parts = link.split(";")
                if len(parts) == 2 and parts[1].strip() == 'rel="next"':
                    next_link = parts[0].strip("<>")
                    break
            # logger.info(f"Next: {next_link}, resp: {resp}, headers: {resp.headers}")
            yield resp.json()

            # Will also sleep
            self._check_ratelimit(resp)

    def pull_comments(
        self,
        post: str,
        include_all: bool = False,
        only_first: bool = False,
        top_num: int = 40,
    ):
        self.__check_login()

        """Return the top_num oldest (or all) replies to a post."""
        top_num = int(top_num)
        if top_num < 1: return

        post = post.split("/")[-1]
        n_output = 0
        for followers_batch in self._get_paginated(
            f"/v1/statuses/{post}/context/descendants",
            resume=None,
            params=dict(sort="oldest"),
        ):
            for f in followers_batch:
                if (only_first and f["in_reply_to_id"] == post) or not only_first:
                    yield f
                    n_output += 1
                    if not include_all and n_output >= top_num: return # break early

    def get_auth_id(self, username: str, password: str) -> str:
        """Logs in to Truth account and returns the session token"""
        url = BASE_URL + "/oauth/token"
        try:
            payload = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "password",
                "username": username,
                "password": password,
                "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                "scope": "read",
            }

            sess_req = requests.request(
                "POST",
                url,
                json=payload,
                proxies=proxies,
                impersonate="chrome123",
                headers={
                    "User-Agent": USER_AGENT,
                },
            )
            sess_req.raise_for_status()
        except requests.RequestsError as e:
            logger.error(f"Failed login request: {str(e)}")
            raise LoginErrorException('Cannot authenticate to .')

        if not sess_req.json()["access_token"]:
            raise ValueError("Invalid truthsocial.com credentials provided!")

        return sess_req.json()["access_token"]
    