"""入口文件"""

from nonebot import require, get_driver
from nonebot.plugin import PluginMetadata, on_notice, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.permission import (
    GROUP_ADMIN,
    GROUP_OWNER,
)

require('nonebot_plugin_localstore')
require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler

from .config import Config, utils
from .handle import eventmonitor

driver = get_driver()


@driver.on_bot_connect
async def _() -> None:
    await utils.init()
    await eventmonitor.check_plugin()


# 戳一戳
chuo = on_notice(
    rule=utils.poke,
    priority=10,
    block=False,
    handlers=[eventmonitor.chuo],
)
# 群员减少
del_user = on_notice(
    rule=utils.del_user,
    priority=50,
    block=False,
    handlers=[eventmonitor.del_user],
)
# 群员增加
add_user = on_notice(
    rule=utils.add_user,
    priority=50,
    block=False,
    handlers=[eventmonitor.add_user],
)
# 群管理
group_admin = on_notice(
    rule=utils.admin_change,
    priority=50,
    block=False,
    handlers=[eventmonitor.admin_chance],
)

on_command(
    '开启',
    aliases={'关闭'},
    priority=10,
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    block=True,
    handlers=[eventmonitor.switch],
)

on_command(
    'eventstatus',
    aliases={'event配置'},
    permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
    priority=10,
    block=False,
    handlers=[eventmonitor.state],
)


on_command(
    'event帮助',
    aliases={'eventhelp'},
    priority=20,
    block=False,
    handlers=[eventmonitor.usage],
)


__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-eventmonitor',
    description='监控群事件的插件，支持戳一戳，成员变动，群荣誉变化等提示的插件',
    usage=utils.usage,
    type='application',
    config=Config,
    homepage='https://github.com/Reversedeer/nonebot_plugin_eventmonitor',
    supported_adapters={'~onebot.v11'},
    extra={
        'author': 'Reversedeer',
        'version': '0.4.8',
        'priority': 50,
        'email': 'ysjvillmark@gmail.com',
    },
)
