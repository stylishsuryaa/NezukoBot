from asyncio import Lock, create_task
from time import time

from pyrogram import filters
from pyrogram.types import Message

from wbb import SUDOERS, USERBOT_PREFIX, app2, eor
from wbb.core.sections import bold, section, w

tasks = {}
TASKS_LOCK = Lock()
arrow = lambda x: x.text + "\n`→`"


def all_tasks():
    return tasks


async def add_task(
    taskFunc,
    task_name,
    *args,
    **kwargs,
):

    async with TASKS_LOCK:
        global tasks

        task_id = (list(tasks.keys())[-1] + 1) if tasks else 0

        task = create_task(
            taskFunc(*args, **kwargs),
            name=task_name,
        )
        tasks[task_id] = task, int(time())
    return task, task_id


async def rm_task(task_id=None):
    global tasks

    async with TASKS_LOCK:
        for key, value in list(tasks.items()):
            if value[0].done() or value[0].cancelled():
                del tasks[key]

        if task_id is not None:
            if task_id in tasks:
                if not tasks[task_id][0].done():
                    tasks[task_id][0].cancel()
                del tasks[task_id]


@app2.on_message(
    filters.user(SUDOERS)
    & ~filters.forwarded
    & ~filters.via_bot
    & filters.command("cancelTask", prefixes=USERBOT_PREFIX)
)
async def task_cancel(_, message: Message):
    m = message
    if len(message.text.split()) != 2:
        return await m.delete()

    task_id = int(m.text.split(None, 1)[1])

    tasks = all_tasks()

    if task_id not in tasks:
        return await m.delete()

    await rm_task(task_id)
    await eor(message, text=f"{arrow(m)} Task cancelled")


@app2.on_message(
    filters.user(SUDOERS)
    & ~filters.forwarded
    & ~filters.via_bot
    & filters.command("lsTasks", prefixes=USERBOT_PREFIX)
)
async def task_list(_, message: Message):
    await rm_task()  # Clean completed tasks

    tasks = all_tasks()

    if not tasks:
        return await eor(
            message,
            text=f"{arrow(message)} No tasks pending",
        )

    text = bold("Tasks") + "\n"

    for i, task in enumerate(list(tasks.items())):
        indent = w * 4

        t, started = task[1]
        elapsed = round(time() - started)
        info = t._repr_info()

        id = task[0]

        text += section(
            f"{indent}Task {i}",
            body={
                "Name": t.get_name(),
                "Task ID": id,
                "Status": info[0].capitalize(),
                "Origin": info[2].split("/")[-1].replace(">", ""),
                "Running since": f"{elapsed}s",
            },
            indent=6,
        )

    await eor(message, text=text)