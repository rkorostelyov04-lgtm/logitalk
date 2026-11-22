import json
import socket
import threading
import tkinter as tk
from datetime import datetime
from tkinter import simpledialog

PORT = 8080
ROOMS = ['Загальний', 'Ідеї', 'Меми']
ACCENT = '#C2410C'
THEMES = {
    'light': {'bg': '#E4DCCB', 'panel': '#FFFFFF', 'mine': '#F5D9A8', 'text': '#14110D', 'muted': '#5E5547'},
    'dark': {'bg': '#0F0E0C', 'panel': '#26231F', 'mine': '#5B4421', 'text': '#F8F4EC', 'muted': '#BDB4A3'},
}
theme = 'dark'

root = tk.Tk()
root.title('LogiTalk')
root.geometry('700x500')

name = simpledialog.askstring('LogiTalk', 'Ім’я:') or 'Гість'
host = simpledialog.askstring('LogiTalk', 'Сервер:', initialvalue='127.0.0.1') or '127.0.0.1'
sock = socket.create_connection((host, PORT))

messages = {room: [] for room in ROOMS}
current = ROOMS[0]
buttons = {}

top = tk.Frame(root)
top.pack(fill='x')
for room in ROOMS:
    buttons[room] = tk.Button(top, text=room, relief='flat', padx=16, pady=8,
                              command=lambda r=room: switch(r))
    buttons[room].pack(side='left')
toggle = tk.Button(top, relief='flat', padx=16, pady=8, command=lambda: set_theme('light' if theme == 'dark' else 'dark'))
toggle.pack(side='right')

chat = tk.Text(root, state='disabled', wrap='word', relief='flat', highlightthickness=0,
               padx=10, pady=10, font=('Segoe UI', 11))
chat.pack(fill='both', expand=True)
chat.tag_config('mine', justify='right', lmargin1=160, lmargin2=160, rmargin=10)
chat.tag_config('other', justify='left', lmargin1=10, lmargin2=10, rmargin=160)
chat.tag_config('who', font=('Segoe UI', 11, 'bold'))
chat.tag_config('time', font=('Segoe UI', 9))

entry = tk.Entry(root, relief='flat', highlightthickness=0, font=('Segoe UI', 12))
entry.pack(fill='x', padx=10, pady=10, ipady=8)


def set_theme(value):
    global theme
    theme = value
    t = THEMES[theme]
    root.config(bg=t['bg'])
    top.config(bg=t['panel'])
    toggle.config(text='☀' if theme == 'dark' else '☾', bg=t['panel'], fg=t['text'], activebackground=t['bg'])
    chat.config(bg=t['bg'], fg=t['text'])
    chat.tag_config('mine', background=t['mine'], foreground=t['text'])
    chat.tag_config('other', background=t['panel'], foreground=t['text'])
    chat.tag_config('time', foreground=t['muted'])
    entry.config(bg=t['panel'], fg=t['text'], insertbackground=t['text'])
    for room, button in buttons.items():
        selected = room == current
        button.config(bg=ACCENT if selected else t['panel'], fg='white' if selected else t['text'],
                      activebackground=ACCENT if selected else t['bg'], activeforeground=t['text'])


def add(msg):
    tag = 'mine' if msg['name'] == name else 'other'
    chat.config(state='normal')
    chat.insert('end', msg['name'] + '  ', (tag, 'who'))
    chat.insert('end', msg['time'] + '\n', (tag, 'time'))
    chat.insert('end', msg['text'] + '\n\n', tag)
    chat.config(state='disabled')
    chat.see('end')


def switch(room):
    global current
    current = room
    buttons[room].config(text=room)
    set_theme(theme)
    chat.config(state='normal')
    chat.delete('1.0', 'end')
    chat.config(state='disabled')
    for msg in messages[room]:
        add(msg)


def got(msg):
    messages[msg['room']].append(msg)
    if msg['room'] == current:
        add(msg)
    else:
        buttons[msg['room']].config(text=msg['room'] + ' •')


def receive():
    for line in sock.makefile(encoding='utf-8'):
        try:
            msg = json.loads(line)
            if msg['room'] in messages:
                root.after(0, got, msg)
        except (ValueError, KeyError, TypeError):
            pass


def send(event=None):
    text = entry.get().strip()
    if text:
        msg = {'room': current, 'name': name, 'text': text[:2000],
               'time': datetime.now().strftime('%H:%M')}
        sock.sendall((json.dumps(msg, ensure_ascii=False) + '\n').encode('utf-8'))
        got(msg)
        entry.delete(0, 'end')


entry.bind('<Return>', send)
switch(current)
threading.Thread(target=receive, daemon=True).start()
root.mainloop()