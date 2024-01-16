# 導入Discord.py模組
import discord
import asyncio
import requests
import random
import html
from googletrans import Translator
from datetime import datetime, timedelta
from datetime import timezone, timedelta
# 導入commands指令模組
from discord.ext import commands
from random import randint
# intents是要求機器人的權限
intents = discord.Intents.all()
#setting
activity = discord.Game(name="一念逍遙")
translator = Translator()
# command_prefix是前綴符號，可以自由選擇($, #, &...)
bot = commands.Bot(command_prefix="%", intents=intents)
@bot.event
# 當機器人完成啟動
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.command(name='ping',help='看看機器人在不在')
# 輸入%ping呼叫指令
async def ping(ctx):
    # 回覆pong!
    await ctx.send("pong!")

@bot.command(name='hi',help='跟機器人打招呼')
async def hi(ctx):
    await ctx.send("嗨!")

@bot.command()
async def guess(ctx):
    '''猜數字遊戲'''
    def is_valid(m):
        return m.author == ctx.author and m.content.isdigit()

    await ctx.send('從哪個數字?')
    min_value_msg = await bot.wait_for('message', check=is_valid)
    min_value = int(min_value_msg.content)

    await ctx.send('到哪個數字?')
    max_value_msg = await bot.wait_for('message', check=is_valid)
    max_value = int(max_value_msg.content)

    secret = randint(min_value, max_value)
    msg = f'猜一個數字在 {min_value} 與 {max_value} 之間'
    counter = 0

    while True:
        counter += 1
        await ctx.send(msg)
        answer_msg = await bot.wait_for('message', check=is_valid)
        answer = int(answer_msg.content)

        if answer > secret:
            msg = '太大了'
        elif answer < secret:
            msg = '太小了'
        else:
            break

    await ctx.send(f'你花了 {counter} 次就猜中了正確數字！')

reminders = {}  # 用來儲存提醒事件的字典

@bot.command(name='time',help='設定時間提醒（目前功能開發中因此只會提醒一次）')
async def time(ctx):
    await ctx.send("請輸入事件名稱/事件時間 (格式: 事件名稱/小時:分鐘)")

    def is_valid(m):
        return m.author == ctx.author

    response_msg = await bot.wait_for('message', check=is_valid)
    response = response_msg.content.split('/')

    if len(response) != 2:
        await ctx.send("格式錯誤，請重新輸入。")
        return

    event_name, event_time = response[0], response[1]

    try:
        event_time_parts = event_time.split(':')
        if len(event_time_parts) != 2:
            raise ValueError
        hours, minutes = map(int, event_time_parts)
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
        event_datetime = datetime.now().replace(hour=hours, minute=minutes, second=0, microsecond=0, tzinfo=timezone(timedelta(hours=8)))
    except ValueError:
        await ctx.send("時間格式錯誤，請重新輸入。")
        return

    reminder_time = (event_datetime - datetime.utcnow().replace(tzinfo=timezone.utc)).total_seconds()
    if reminder_time < 0:
        await ctx.send("無效的時間，請重新輸入。")
        return

    reminders[event_name] = {
        'time': reminder_time,
        'event_datetime': event_datetime,
        'ctx': ctx,
        'event_msg': f"提醒：{event_name} 的時間到了！"
    }
    await ctx.send(f"已設定提醒：{event_name}")

@bot.command(name='time_remove',help='移除時間提醒')
async def time_remove(ctx):
    reminders.clear()
    await ctx.send("已移除所有提醒事件。")

@bot.command(name='time_list',help='列出所有時間提醒')
async def time_list(ctx):
    if not reminders:
        await ctx.send("目前沒有任何提醒。")
    else:
        reminder_list = "\n".join([f"{event_name}: {reminder_data['event_datetime']}" for event_name, reminder_data in reminders.items()])
        await ctx.send(f"目前的提醒列表：\n{reminder_list}")

@bot.command(name='指令列表', help='列出所有存在的指令')
async def custom_command_list(ctx):
      command_list = [f"{command.name}: {command.help}" for command in sorted(bot.commands, key=lambda x: x.name) if command.name != 'help']
      await ctx.send("目前的指令列表：\r\n" + '\r\n'.join(command_list))
      
@bot.command(name='謎語')
async def riddle_anime(ctx):
    try:
        # 使用 OTDB 獲取謎語問題
        response = requests.get('https://opentdb.com/api.php?amount=1')
        data = response.json()

        if 'results' in data and data['results']:
            # 獲取謎語相關信息
            riddle_info = data['results'][0]
            question = html.unescape(riddle_info['question'])
            answers = riddle_info['incorrect_answers'] + [riddle_info['correct_answer']]
            random.shuffle(answers)

            try:
                translated_question = translator.translate(question, dest='zh-TW').text
                translated_answers = [translator.translate(answer, dest='zh-TW').text for answer in answers]
            except Exception as e:
                await ctx.send(f"翻譯時發生錯誤：{e}")
                return

            # 發送翻譯後的謎語問題到 Discord 伺服器
        await ctx.send(f"謎語問題：{translated_question}")
        await ctx.send("選項： " + ', '.join(translated_answers))

        # 等待使用者回應
        def check_answer(m):
            return m.author == ctx.author and m.content.isdigit()

        answer_msg = await bot.wait_for('message', check=check_answer)
        user_answer = int(answer_msg.content)

        # 比對答案
        correct_answer_index = translated_answers.index(translator.translate(riddle_info['correct_answer'], dest='zh-TW').text)
        correct_answer = answers[correct_answer_index]

        if user_answer == correct_answer_index + 1:
            await ctx.send("答對了！正確答案是：{}".format(correct_answer))
        else:
            await ctx.send("答錯了！正確答案是：{}".format(correct_answer))

    except Exception as e:
        # 處理其他可能的異常
        await ctx.send(f"發生錯誤：{e}")
# 在on_ready事件處理新增一個循環來處理提醒
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    async def reminder_loop():
        while True:
            await asyncio.sleep(1)
            to_remove = []
            current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            for event_name in list(reminders.keys()):
                reminder_data = reminders[event_name]
                if current_time >= reminder_data['event_datetime']:
                    await reminder_data['ctx'].send(reminder_data['event_msg'])
                    to_remove.append(event_name)

            for event_name in to_remove:
                reminders.pop(event_name, None)

    bot.loop.create_task(reminder_loop())

bot.run('MTE5NjI5OTk3NTMyMDE1MDA3Ng.GVorVR.MhCt6Cw8b_Xbv7hgIxHJtSiTrMfo-Ws_cfjkcY')