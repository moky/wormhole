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

from typing import Optional, AnyStr, Dict

from aiohttp.typedefs import StrOrURL, LooseHeaders
from aiohttp.abc import AbstractCookieJar
from aiohttp import CookieJar, ClientSession, ClientResponse


class HttpResponse:

    def __init__(self, headers: Dict, status: int, data: Optional[bytes], encoding: Optional[str]):
        super().__init__()
        self.__headers = headers
        self.__status = status
        self.__data = data
        self.__encoding = encoding

    @property
    def headers(self) -> Dict[str, str]:
        return self.__headers

    def get_header(self, key: str) -> Optional[str]:
        headers = self.headers
        if headers is None:
            return None
        value = headers.get(key)
        if value is not None:
            # exactly
            return value
        # case insensitive
        lower = key.strip().lower()
        for name in headers:
            if name.strip().lower() == lower:
                return headers.get(name)

    @property
    def status(self) -> int:
        return self.__status

    @property
    def data(self) -> Optional[bytes]:
        return self.__data

    @property
    def encoding(self) -> Optional[str]:
        return self.__encoding

    @property
    def text(self) -> Optional[str]:
        data = self.data
        encoding = self.encoding
        if data is None or encoding is None:
            return None
        else:
            return data.decode(self.encoding)

    @classmethod
    async def extract(cls, response: ClientResponse):
        headers = response.headers
        status = response.status
        if response.ok:  # status code: 2xx
            data = await response.read()
            encoding = response.get_encoding()
        else:
            data = None
            encoding = None
        return cls(headers=headers, status=status, data=data, encoding=encoding)


class HttpSession:

    def __init__(self, cookie_jar: AbstractCookieJar = None):
        super().__init__()
        self.__cookie_jar = CookieJar() if cookie_jar is None else cookie_jar

    @property
    def cookie_jar(self) -> AbstractCookieJar:
        return self.__cookie_jar

    async def http_head(self, url: StrOrURL, *, headers: LooseHeaders = None, timeout: float = None,
                        allow_redirects: bool = False) -> Optional[HttpResponse]:
        try:
            async with ClientSession(headers=headers, conn_timeout=timeout, cookie_jar=self.cookie_jar) as session:
                async with session.head(url=url, allow_redirects=allow_redirects) as response:
                    return await HttpResponse.extract(response=response)
        except Exception as error:
            print('[HTTP] failed to HEAD: %s , error: %s' % (url, error))

    async def http_get(self, url: StrOrURL, *, headers: LooseHeaders = None, timeout: float = None,
                       allow_redirects: bool = True) -> Optional[HttpResponse]:
        try:
            async with ClientSession(headers=headers, conn_timeout=timeout, cookie_jar=self.cookie_jar) as session:
                async with session.get(url=url, allow_redirects=allow_redirects) as response:
                    return await HttpResponse.extract(response=response)
        except Exception as error:
            print('[HTTP] failed to GET: %s , error: %s' % (url, error))

    async def http_post(self, url: StrOrURL, *, data: AnyStr,
                        headers: LooseHeaders = None, timeout: float = None) -> Optional[HttpResponse]:
        try:
            async with ClientSession(headers=headers, conn_timeout=timeout, cookie_jar=self.cookie_jar) as session:
                async with session.post(url=url, data=data) as response:
                    return await HttpResponse.extract(response=response)
        except Exception as error:
            print('[HTTP] failed to POST (%d bytes): %s , error: %s' % (len(data), url, error))
