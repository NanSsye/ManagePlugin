import tomllib

from tabulate import tabulate

from WechatAPI import WechatAPIClient
from database.XYBotDB import XYBotDB
from utils.decorators import *
from utils.plugin_base import PluginBase
from utils.plugin_manager import plugin_manager


class ManagePlugin(PluginBase):
    description = "插件管理器"
    author = "xxxbot"
    version = "1.1.0"

    def __init__(self):
        super().__init__()

        self.db = XYBotDB()

        with open("plugins/ManagePlugin/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)

        with open("main_config.toml", "rb") as f:
            main_config = tomllib.load(f)

        plugin_config = plugin_config["ManagePlugin"]
        main_config = main_config["XYBot"]

        self.command = plugin_config["command"]
        self.admins = main_config["admins"]

    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        content = str(message["Content"]).strip()
        command = content.split(" ")

        if not len(command) or command[0] not in self.command:
            return True  # 不是管理命令，继续执行后续处理

        if message["SenderWxid"] not in self.admins:
            await bot.send_text_message(message["FromWxid"], "你没有权限使用此命令")
            return False  # 阻止后续处理

        plugin_name = command[1] if len(command) > 1 else None
        if command[0] == "加载插件":
            if plugin_name in plugin_manager.plugins.keys():
                await bot.send_text_message(message["FromWxid"], "⚠️插件已经加载")
                return False  # 阻止后续处理

            attempt = await plugin_manager.load_plugin_from_directory(bot, plugin_name)
            if attempt:
                await bot.send_text_message(message["FromWxid"], f"✅插件 {plugin_name} 加载成功")
            else:
                await bot.send_text_message(message["FromWxid"], f"❌插件 {plugin_name} 加载失败，请查看日志错误信息")

        elif command[0] == "加载所有插件":
            attempt = await plugin_manager.load_plugins_from_directory(bot)
            if attempt:
                attempt_str = '\n'.join(attempt)
                await bot.send_text_message(message["FromWxid"], f"✅插件加载成功：\n{attempt_str}")
            else:
                await bot.send_text_message(message["FromWxid"], "❌没有成功加载任何插件，请查看日志了解更多信息")

        elif command[0] == "卸载插件":
            if plugin_name == "ManagePlugin":
                await bot.send_text_message(message["FromWxid"], "⚠️你不能卸载 ManagePlugin 插件！")
                return False  # 阻止后续处理
            elif plugin_name not in plugin_manager.plugins.keys():
                await bot.send_text_message(message["FromWxid"], "⚠️插件不存在或未加载")
                return False  # 阻止后续处理

            # 调用 unload_plugin 方法并设置 add_to_excluded 参数为 True
            # 这样会将插件添加到禁用列表中并保存到配置文件
            attempt = await plugin_manager.unload_plugin(plugin_name, add_to_excluded=True)
            if attempt:
                await bot.send_text_message(message["FromWxid"], f"✅插件 {plugin_name} 卸载成功")
            else:
                await bot.send_text_message(message["FromWxid"], f"❌插件 {plugin_name} 卸载失败，请查看日志错误信息")

        elif command[0] == "卸载所有插件":
            unloaded_plugins, failed_unloads = await plugin_manager.unload_all_plugins()
            unloaded_plugins = '\n'.join(unloaded_plugins)
            failed_unloads = '\n'.join(failed_unloads)
            await bot.send_text_message(message["FromWxid"],
                                        f"✅插件卸载成功：\n{unloaded_plugins}\n❌插件卸载失败：\n{failed_unloads}")

        elif command[0] == "重载插件":
            if plugin_name == "ManagePlugin":
                await bot.send_text_message(message["FromWxid"], "⚠️你不能重载 ManagePlugin 插件！")
                return False  # 阻止后续处理
            elif plugin_name not in plugin_manager.plugins.keys():
                await bot.send_text_message(message["FromWxid"], "⚠️插件不存在或未加载")
                return False  # 阻止后续处理

            attempt = await plugin_manager.reload_plugin(bot, plugin_name)
            if attempt:
                await bot.send_text_message(message["FromWxid"], f"✅插件 {plugin_name} 重载成功")
            else:
                await bot.send_text_message(message["FromWxid"], f"❌插件 {plugin_name} 重载失败，请查看日志错误信息")

        elif command[0] == "重载所有插件":
            loaded_plugins, failed_plugins = await plugin_manager.reload_all_plugins(bot)
            
            message_parts = []
            
            if loaded_plugins:
                loaded_plugins_str = '\n'.join(loaded_plugins)
                message_parts.append(f"✅插件重载成功：\n{loaded_plugins_str}")
            else:
                message_parts.append("❌没有成功重载任何插件")
            
            if failed_plugins:
                failed_plugins_str = '\n'.join(failed_plugins)
                message_parts.append(f"❌插件重载失败：\n{failed_plugins_str}")
                
            await bot.send_text_message(message["FromWxid"], "\n\n".join(message_parts))

        elif command[0] == "插件列表":
            plugin_list = plugin_manager.get_plugin_info()

            plugin_stat = [["插件名称", "是否启用"]]
            for plugin in plugin_list:
                plugin_stat.append([plugin['name'], "✅" if plugin['enabled'] else "🚫"])

            table = str(tabulate(plugin_stat, headers="firstrow", tablefmt="simple"))

            await bot.send_text_message(message["FromWxid"], table)

        elif command[0] == "插件信息":
            attemt = plugin_manager.get_plugin_info(plugin_name)
            if isinstance(attemt, dict):
                output = (f"插件名称: {attemt['name']}\n"
                          f"插件描述: {attemt['description']}\n"
                          f"插件作者: {attemt['author']}\n"
                          f"插件版本: {attemt['version']}")

                await bot.send_text_message(message["FromWxid"], output)
            else:
                await bot.send_text_message(message["FromWxid"], "⚠️插件不存在或未加载")

        return False  # 所有命令处理完成后阻止后续处理