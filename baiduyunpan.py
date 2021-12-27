#!/usr/local/python3/bin/python3.5
# -*- coding:utf-8 -*-


import re
import json
import asyncio
import aiohttp
import argparse
import traceback
import pandas as pd


cookies = {
    "BDUSS": "",
    "STOKEN": ""
}

headers = {
    "Host": "pan.baidu.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
}

BAIDU_STATIC_PARAMETER = {
    "gid": ""
    "type": "2",
    "channel": "chunlei",
    "web": "1",
    "app_id": "250528",
    "clienttype": "0",
    "logid": "MTY0MDA2OTEzNzU4NzAuNDU4MzY5NDUyNDAzMTU2Mw=="
}

dirStructure = {}
dirList = []


async def verifyCookie(session):
    async with session.get("https://pan.baidu.com") as resp:
        reqBody = await resp.text()
        r = re.compile('.*bdstoken":"([a-z0-9]{32}).*')
        bdstoken = r.findall(reqBody)
        if bdstoken:
            BAIDU_STATIC_PARAMETER['bdstoken'] = bdstoken[0]


async def groupFile(session):
    limit = 50
    desc = 1
    gid = BAIDU_STATIC_PARAMETER['gid']
    bdstoken = BAIDU_STATIC_PARAMETER['bdstoken']
    type = BAIDU_STATIC_PARAMETER['type']
    channel = BAIDU_STATIC_PARAMETER['channel']
    web = BAIDU_STATIC_PARAMETER['web']
    app_id = BAIDU_STATIC_PARAMETER['app_id']
    logid = BAIDU_STATIC_PARAMETER['logid']
    clienttype = BAIDU_STATIC_PARAMETER['clienttype']

    url = f'''https://pan.baidu.com/mbox/group/listshare? \
              gid={gid}& \
              limit={limit}& \
              desc={desc}& \
              type={type}& \
              bdstoken={bdstoken}& \
              channel={channel}& \
              web={web}& \
              app_id={app_id}& \
              logid={logid}& \
              clienttype={clienttype}'''

    async with session.get(url) as resp:
        reqBody = await resp.json()

    rootDir = {}
    for i in reqBody['records']['msg_list']:
        rootDir[i['msg_id']] = {
            "fs_id": i['file_list'][0]['fs_id'],
            "uk": i['uk'],
            "server_filename": i['file_list'][0]['server_filename'],
            "isdir": int(i['file_list'][0]['isdir'])
        }
    return rootDir


async def listDir(session, msg_id, uk, fs_id, isdir, parentFsId=[]):
    if not parentFsId:
        parentFsId = [fs_id]
    if isdir == 1:
        msg_id = msg_id
        page = "1"
        num = "200"
        fs_id = fs_id
        from_uk = uk
        gid = BAIDU_STATIC_PARAMETER['gid']
        bdstoken = BAIDU_STATIC_PARAMETER['bdstoken']
        type = BAIDU_STATIC_PARAMETER['type']
        channel = BAIDU_STATIC_PARAMETER['channel']
        web = BAIDU_STATIC_PARAMETER['web']
        app_id = BAIDU_STATIC_PARAMETER['app_id']
        logid = BAIDU_STATIC_PARAMETER['logid']
        clienttype = BAIDU_STATIC_PARAMETER['clienttype']

        url = f'''https://pan.baidu.com/mbox/msg/shareinfo? \
                msg_id={msg_id}& \
                page={page}& \
                from_uk={from_uk}& \
                gid={gid}& \
                type={type}& \
                fs_id={fs_id}& \
                num={num}& \
                bdstoken={bdstoken}& \
                channel={channel}& \
                web={web}& \
                app_id={app_id}& \
                logid={logid}& \
                clienttype={clienttype}'''

        async with session.get(url) as resp:
            reqBody = await resp.read()
            try:
                reqBody = json.loads(reqBody)
            except Exception:
                reqBody = {
                    "records": []
                }
            for i in reqBody['records']:
                tempDirStructure = dirStructure[msg_id]
                for id in parentFsId:
                    tempDirStructure = tempDirStructure[id]['subdir']
                if i['isdir'] == 1:
                    tempDirStructure[str(i['fs_id'])] = {
                        "isdir": i['isdir'],
                        "server_filename": i['server_filename'].replace('\xa0', ' '),
                        "subdir": {}
                    }
                    parentFsId.append(str(i['fs_id']))
                    await listDir(session, msg_id, uk, str(i['fs_id']), i['isdir'], parentFsId)
                else:
                    tempDirStructure[str(i['fs_id'])] = {
                        "isdir": i['isdir'],
                        "server_filename": i['server_filename'].replace('\xa0', ' ')
                    }
                    filePath = []
                    temp1DirStructure = dirStructure[msg_id]
                    for pFsId in parentFsId:
                        filePath.append(temp1DirStructure[pFsId]['server_filename'])
                        temp1DirStructure = temp1DirStructure[pFsId]['subdir']
                    filePath.append(i['server_filename'].replace('\xa0', ' '))
                    dirList.append(filePath)
            parentFsId.pop()


async def main():
    s = aiohttp.ClientSession(cookies=cookies, headers=headers)
    try:
        await verifyCookie(s)
        rootDir = await groupFile(s)
        tasks = []
        for msg_id in rootDir.keys():
            if rootDir[msg_id]['isdir'] == 1:
                dirStructure[msg_id] = {}
                dirStructure[msg_id][rootDir[msg_id]['fs_id']] = {
                    "fs_id": rootDir[msg_id]['fs_id'],
                    "uk": rootDir[msg_id]['uk'],
                    "server_filename": rootDir[msg_id]['server_filename'],
                    "isdir": rootDir[msg_id]['isdir'],
                    "subdir": {}
                }
                tasks.append(asyncio.ensure_future(listDir(
                    s, msg_id, rootDir[msg_id]['uk'],
                    rootDir[msg_id]['fs_id'],
                    rootDir[msg_id]['isdir']
                )))
        await asyncio.wait(tasks)
    except Exception:
        traceback.print_exc()
    finally:
        await s.close()


def doSearch(cacheFile, searchStr):
    with open(cacheFile) as f:
        searchFile = eval(f.read())

    searchFileJoin = ['\\'.join(i) for i in searchFile]
    df = pd.DataFrame(searchFileJoin, columns=['name'])
    result = df[df['name'].str.contains(searchStr)]
    return result.values


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="百度云群分享文件搜索")
    parser.add_argument('--search', '-s', help='搜索字符串')
    parser.add_argument('--update', '-u', help='是否更新本地群文件缓存列表', default='False', choices=['True', 'False'])
    parser.add_argument('--cache-file', help='指定已存在的本地群分享缓存文件', default='./baiduyun_dirList.json')
    args = parser.parse_args()

    if args.update == 'True':
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        with open(args.cache_file, 'w') as f:
            f.write(str(dirList))

    if args.search:
        searchResult = doSearch(args.cache_file, args.search)
        for i in searchResult:
            print(i[0])

    if not args.search and args.update == 'False':
        parser.print_help()
