# -*- coding: utf-8 -*-
#
#   Async HTTP
#
#                                Written in 2024 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import threading
import time
from typing import Optional, AnyStr, Dict

from yarl import URL

from ..mem import CacheManager

from .session import HttpSession, HttpResponse


class HttpClient:

    def __init__(self, base_url: str = None, session: HttpSession = None):
        super().__init__()
        self.__base = base_url
        self.__session = HttpSession() if session is None else session

    @property
    def base_url(self) -> Optional[str]:
        return self.__base

    #
    #   Cookies
    #

    @property
    def cookies(self) -> Optional[Dict]:
        cookie_jar = self.__session.cookie_jar
        base_url = self.base_url
        if base_url is not None:
            request_url = URL(base_url)
            return cookie_jar.filter_cookies(request_url=request_url)

    def set_cookie(self, key: str, value: str):
        cookie_jar = self.__session.cookie_jar
        cookie_jar.update_cookies({
            key: value,
        })

    def get_cookie(self, key: str) -> Optional[str]:
        cookies = self.cookies
        if cookies:
            return cookies.get(key)

    def clear_cookies(self):
        cookie_jar = self.__session.cookie_jar
        cookie_jar.clear()

    #
    #   Requests
    #

    async def http_head(self, url: str, *, headers: Dict = None, timeout: float = None,
                        allow_redirects: bool = False) -> Optional[HttpResponse]:
        session = self.__session
        return await session.http_head(url=url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)

    async def http_get(self, url: str, *, headers: Dict = None, timeout: float = None,
                       allow_redirects: bool = True) -> Optional[HttpResponse]:
        url = self._get_url(url=url)
        session = self.__session
        return await session.http_get(url=url, headers=headers, timeout=timeout, allow_redirects=allow_redirects)

    async def http_post(self, url: str, *, data: AnyStr,
                        headers: Dict = None, timeout: float = None) -> Optional[HttpResponse]:
        url = self._get_url(url=url)
        session = self.__session
        return await session.http_post(url=url, data=data, headers=headers, timeout=timeout)

    def _get_url(self, url: str) -> str:
        base = self.__base
        return url if base is None else full_url(url=url, base=base)

    #
    #   Factory
    #

    @classmethod
    def create(cls, base_url: str = None, session: HttpSession = None, expires: float = None):
        return CachedClient(base_url=base_url, session=session, expires=expires)


def full_url(url: str, base: str) -> str:
    pos = url.find(r'://')
    if pos > 0:
        # full url
        return url
    elif url.startswith(r'/'):
        # absolute path
        pos = base.find(r'/', pos + 3)
        if pos > 0:
            base = base[:pos]
    else:
        # related path
        if url.startswith(r'./'):
            url = url[2:]
        if not base.endswith(r'/'):
            base += r'/'
    # join
    return '%s%s' % (base, url)


class CachedClient(HttpClient):

    CACHE_EXPIRES = 60 * 8  # seconds
    CACHE_REFRESHING = 128  # seconds

    def __init__(self, base_url: str = None, session: HttpSession = None, expires: float = None):
        super().__init__(base_url=base_url, session=session)
        self.__expires = self.CACHE_EXPIRES if expires is None else expires
        self.__refresh = self.CACHE_REFRESHING
        self.__caches = CacheManager().get_pool(name='aiou_http_caches')  # url => html
        self.__lock = threading.Lock()

    @property
    def expires_duration(self) -> float:
        return self.__expires

    @property
    def refreshing_duration(self) -> float:
        return self.__refresh

    # Override
    async def http_get(self, url: str, *, headers: Dict = None, timeout: float = None,
                       allow_redirects: bool = True) -> Optional[HttpResponse]:
        now = time.time()
        #
        #  1. check memory cache
        #
        value, holder = self.__caches.fetch(key=url, now=now)
        if value is not None:
            # got it from cache
            return value
        elif holder is None:
            # holder not exists, means it is the first querying
            pass
        elif holder.is_alive(now=now):
            # holder is not expired yet,
            # means the value is actually empty,
            # no need to check it again.
            return None
        #
        #  2. lock for querying
        #
        with self.__lock:
            # locked, check again to make sure the cache not exists.
            # (maybe the cache was updated by other threads while waiting the lock)
            value, holder = self.__caches.fetch(key=url, now=now)
            if value is not None:
                return value
            elif holder is None:
                pass
            elif holder.is_alive(now=now):
                return None
            else:
                # holder exists, renew the expired time for other threads
                holder.renewal(duration=self.refreshing_duration, now=now)
            # 2.1. query remote server
            value = await super().http_get(url=url, headers=headers)
            # 2.2. update memory cache
            self.__caches.update(key=url, value=value, life_span=self.expires_duration, now=now)
        #
        #  3. OK, return cached value
        #
        return value
