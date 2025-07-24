"""事件处理"""

import json
import asyncio

from httpx import AsyncClient, ConnectError, RequestError, HTTPStatusError
from nonebot import get_bot
from packaging import version
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    PokeNotifyEvent,
    HonorNotifyEvent,
    GroupMessageEvent,
    LuckyKingNotifyEvent,
    GroupAdminNoticeEvent,
    GroupUploadNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
)

from .config import utils, config_data
from .matcher import message
from .txt2img import txt_to_img


class Eventmonitor:
    async def chuo(
        self,
        matcher: Matcher,
        event: PokeNotifyEvent,
    ) -> None:
        """戳一戳"""
        if not (await utils.check_chuo(utils.g_temp, str(event.group_id))):
            return
        # 获取用户id
        uid: str = event.get_user_id()
        try:
            cd = event.time - utils.chuo_CD_dir[uid]
        except KeyError:
            # 没有记录则cd为cd_time+1
            cd: int = config_data.event_chuo_cd + 1
        if cd > config_data.event_chuo_cd or event.get_user_id() in config_data.superusers:
            utils.chuo_CD_dir.update({uid: event.time})
            rely_msg: str = await message.chuo_send_msg()
            if await utils.check_txt_to_img(config_data.event_check_txt_img):
                await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(str(rely_msg))))
            else:
                await matcher.finish(rely_msg)

    async def del_user(
        self,
        matcher: Matcher,
        event: GroupDecreaseNoticeEvent,
        bot: Bot,
    ) -> None:
        """退群事件"""
        if not (await utils.check_del_user(utils.g_temp, str(event.group_id))):
            return
        user_id: int = event.user_id
        member_info: dict = await bot.get_stranger_info(user_id=user_id)
        nickname: str = member_info.get('nickname', '未知昵称')
        rely_msg: str | Message = await message.del_user_bye(event.time, event.user_id, nickname)
        if await utils.check_txt_to_img(config_data.event_check_txt_img):
            await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(str(rely_msg))), at_sender=True)
        else:
            await matcher.finish(rely_msg)

    async def add_user(
        self,
        matcher: Matcher,
        event: GroupIncreaseNoticeEvent,
        bot: Bot,
    ) -> None:
        """入群事件"""
        await utils.config_check()
        if not (await utils.check_add_user(utils.g_temp, str(event.group_id))):
            return
        bot_qq = int(bot.self_id)
        user_id: int = event.user_id
        group_id: int = event.group_id
        member_info: dict = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        nickname: str = member_info.get('nickname', '未知昵称')
        rely_msg = await message.add_user_wecome(event.time, user_id, bot_qq, nickname)
        if await utils.check_txt_to_img(config_data.event_check_txt_img):
            await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(str(rely_msg))), at_sender=True)
        else:
            await matcher.finish(rely_msg)

    async def admin_chance(
        self,
        matcher: Matcher,
        event: GroupAdminNoticeEvent,
        bot: Bot,
    ) -> None:
        """管理员变动事件"""
        if not (await utils.check_admin(utils.g_temp, str(event.group_id))):
            return
        bot_qq = int(bot.self_id)
        rely_msg: str = await message.admin_changer(event.sub_type, event.user_id, bot_qq)
        if await utils.check_txt_to_img(config_data.event_check_txt_img):
            await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(rely_msg)), at_sender=True)
        else:
            await matcher.finish(rely_msg)


    async def switch(
        self,
        matcher: Matcher,
        event: GroupMessageEvent,
    ) -> None:
        """获取开关指令的参数，即用户输入的指令内容"""
        command = str(event.get_message()).strip()
        # 获取群组ID
        gid = str(event.group_id)
        # 判断指令是否包含"开启"或"关闭"关键字
        if '开启' in command or '开始' in command:
            if key := utils.get_command_type(command):
                utils.g_temp[gid][key] = True
                await utils.write_group_data(utils.g_temp)
                name = utils.get_function_name(key)
                if not (await utils.check_txt_to_img(config_data.event_check_txt_img)):
                    await matcher.finish(f'{name}功能已开启喵')
                else:
                    await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(f'{name}功能已开启喵')))
        elif ('禁止' in command or '关闭' in command) and (key := utils.get_command_type(command)):
            utils.g_temp[gid][key] = False
            await utils.write_group_data(utils.g_temp)
            name = utils.get_function_name(key)
            if await utils.check_txt_to_img(config_data.event_check_txt_img):
                await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(f'{name}功能已关闭喵')))
            else:
                await matcher.finish(f'{name}功能已关闭喵')

    async def usage(self, matcher: Matcher) -> None:
        """获取指令帮助"""
        if await utils.check_txt_to_img(config_data.event_check_txt_img):
            await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(utils.usage)))
        else:
            await matcher.finish(utils.usage)

    async def state(self, matcher: Matcher, event: GroupMessageEvent) -> None:
        """指令开关"""
        gid = str(event.group_id)
        group_status: dict = await utils.load_current_config()
        if gid not in group_status:
            await utils.config_check()
            group_status: dict = await utils.load_current_config()
        rely_msg: str = f'群{gid}的Event配置状态：\n' + '\n'.join(
            [f'{utils.path[func][0]}: {"开启" if group_status[gid][func] else "关闭"}' for func in utils.path]
        )
        if await utils.check_txt_to_img(config_data.event_check_txt_img):
            await matcher.send(MessageSegment.image(await txt_to_img.txt_to_img(rely_msg)))
        else:
            await matcher.finish(rely_msg)



eventmonitor = Eventmonitor()
