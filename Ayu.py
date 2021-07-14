#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# __author__ = 'Lian Tian'
# __email__ = "liantian.me+code@gmail.com"
# python -m nuitka  --module Ayu.py --follow-imports
import time
import logging
import socket
import ssl
from typing import Optional, List
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from icmplib import NameLookupError, ICMPSocketError
from icmplib import SocketAddressError, SocketPermissionError
from icmplib import ping, traceroute
from termcolor import cprint
from tqdm import tqdm

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("net_test.log")
    ]
)


def log(level: str, msg: str, attrs: Optional[List[str]] = None):
    if level.lower().startswith("warn"):
        logging.warning(msg)
        cprint(msg, 'red', attrs=attrs)
    elif level.lower().startswith("suc"):
        logging.warning(msg)
        cprint(msg, 'green', attrs=['bold'])
    elif level.lower().startswith("err"):
        logging.warning(msg)
        cprint(msg, 'red', attrs=['bold', 'reverse', 'blink'])
    else:
        logging.info(msg)
        cprint(msg, "white", attrs=attrs)


def tcp_test(ip: str, port: int):
    log("info", "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    if result == 0:
        log("suc", "IP：{x}，TCP端口：{y}，是打开的".format(x=ip, y=port))
    else:
        log("warn", "IP：{x}，TCP端口：{y}，是关闭的".format(x=ip, y=port))
    sock.close()


def url_test(url: str):
    log("info", "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>")
    req = Request(url)
    log("info", "检测网址打开：{x}".format(x=url), attrs=["bold"])
    try:
        response = urlopen(req, context=ctx)
        log("suc", "HTTP访问正常")
    except HTTPError as e:
        log("suc", "HTTP返回代码：{x}".format(x=e.code))
    except URLError as e:
        log("error", "错误，无法访问网页，错误原因：{x}".format(x=e.reason))


def ping_test(address_list: List[str],
              threshold: float = 10,
              count: int = 5,
              interval: float = 0.5,
              timeout: float = 0.5,
              family: int = 4,
              ):
    """
        address：地址
        threshold: 阈值，单位秒
    """
    if threshold/1000 > timeout - 1.0:
        timeout = threshold/1000 + 1.0
    log("info",
        "正在执行ping测试，总计{x}个地址，预计需要至少{y}秒".format(x=len(address_list), y=int(len(address_list) * count * (interval+timeout))))
    for address in address_list:
        try:
            result = ping(address, count=count, interval=interval, family=family, timeout=timeout)
            log("info", "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>")
            log("info", "主机地址：{x}[{y}]".format(x=address, y=result.address), attrs=['bold'])
            if result.is_alive:
                log("info", "> 状态：网络通")
                if result.packet_loss > 0.0:
                    log("err", "> 发生丢包，丢包率{x:.2f}%".format(x=result.packet_loss * 100))
                else:
                    log("suc", "> 没有丢包")
                if result.avg_rtt > threshold:
                    log("err", "> 平均延时{x:.2f}，大于预定阈值{y:.2f}，网速异常".format(x=result.avg_rtt, y=threshold))
                else:
                    log("suc", "> 平均延时{x:.2f}，小于预定阈值{y:.2f}，网络正常".format(x=result.avg_rtt, y=threshold))
                if result.max_rtt > threshold:
                    log("err", "> 最大延时{x:.2f}，大于预定阈值{y:.2f}，网速异常".format(x=result.max_rtt, y=threshold))
                else:
                    log("suc", "> 最大延时{x:.2f}，小于预定阈值{y:.2f}，网络正常".format(x=result.max_rtt, y=threshold))
            else:
                log("warning", "> 状态：网络不通（全丢包）")
        except NameLookupError:
            log("err", "NameLookupError域名解析错误")
        except SocketPermissionError:
            log("err", "SocketPermissionError")
        except SocketAddressError:
            log("err", "SocketAddressError")
        except ICMPSocketError:
            log("err", "ICMPSocketError错误")


def traceroute_test(address_list: List[str],
                    require_address: Optional[List[str]] = None,
                    count: int = 3,
                    interval: float = 0.1,
                    timeout: float = 1.0,
                    max_hops: int = 30,
                    family: int = 4):
    log("info",
        "正在执行traceroute测试，总计{x}个地址。".format(x=len(address_list)))
    if require_address is None:
        tt = tuple([])
    else:
        tt = tuple(require_address)
    for address in address_list:
        try:
            hops = traceroute(address, count=count, interval=interval, timeout=timeout, max_hops=max_hops,
                              family=family)
            log("info", "<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>")
            log("info", "Traceroute主机地址：{x}".format(x=address), attrs=['bold'])
            match_require_address_count = 0
            for hop in hops:
                if hop.address.startswith(tt):
                    match_require_address_count += 1
                    log("success",
                        '{distance:<10d}{address:<15}{avg_rtt:.2f} ms'.format(distance=hop.distance,
                                                                              address=hop.address,
                                                                              avg_rtt=hop.avg_rtt))
                else:
                    log("info",
                        '{distance:<10d}{address:<15}{avg_rtt:.2f} ms'.format(distance=hop.distance,
                                                                              address=hop.address,
                                                                              avg_rtt=hop.avg_rtt))
            if match_require_address_count > 0:
                log("success", "成功匹配到路由表!")
            if (require_address is not None) and match_require_address_count == 0:
                log("err", "未匹配到路由表")
        except NameLookupError:
            log("err", "NameLookupError域名解析错误")
        except SocketPermissionError:
            log("err", "SocketPermissionError")
        except SocketAddressError:
            log("err", "SocketAddressError")
        except ICMPSocketError:
            log("err", "ICMPSocketError错误")


def pause():
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print('interrupted!')
