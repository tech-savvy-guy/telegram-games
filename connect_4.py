import os
import telebot
import pyrebase
import threading
import schedule
from PIL import Image
from time import time, sleep
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
from telebot.types import InputMediaPhoto
from telebot.types import InlineQueryResultPhoto

config = {                          # Your FIREBASE DATABASE configurations

    "apiKey"              : "",
    "authDomain"          : "",
    "databaseURL"         : "",
    "projectId"           : "",
    "storageBucket"       : "",
    "messagingSenderId"   : "",
    "appId"               : "",
    "measurementId"       : "",   
}

firebase = pyrebase.initialize_app(config)
database = firebase.database()

API_KEY = ""                        # API TOKEN from @BotFather
STORAGE_CHANNEL = 1234567890        # Channel Id for a private storage place

bot = telebot.TeleBot(API_KEY, parse_mode="HTML")           # Initializing the bot
BANNER = ""                                                 # FILE ID of banner for your bot

def connect_4_markup(play, positions):          # Creates the move markup

    game_board, buttons = InlineKeyboardMarkup(row_width = 7), []
    for pos in positions:
        buttons.append(InlineKeyboardButton(play, callback_data=pos))
    game_board.add(*buttons)

    return game_board

def board_img(red, yellow, game_id):            # Creates the board image

    board = Image.open(r"./assets/game_board.jpg")
    p1    = Image.open(r"./assets/p1.png")
    p2    = Image.open(r"./assets/p2.png")

    tiles = {
        "A1" : (0,0), "B1" : (0,0), "C1" : (0,0), "D1" : (0,0), "E1" : (0,0), "F1" : (0,0), "G1" : (0,0),
        "A2" : (0,0), "B2" : (0,0), "C2" : (0,0), "D2" : (0,0), "E2" : (0,0), "F2" : (0,0), "G2" : (0,0),
        "A3" : (0,0), "B3" : (0,0), "C3" : (0,0), "D3" : (0,0), "E3" : (0,0), "F3" : (0,0), "G3" : (0,0),
        "A4" : (0,0), "B4" : (0,0), "C4" : (0,0), "D4" : (0,0), "E4" : (0,0), "F4" : (0,0), "G4" : (0,0),
        "A5" : (0,0), "B5" : (0,0), "C5" : (0,0), "D5" : (0,0), "E5" : (0,0), "F5" : (0,0), "G5" : (0,0),
        "A6" : (0,0), "B6" : (0,0), "C6" : (0,0), "D6" : (0,0), "E6" : (0,0), "F6" : (0,0), "G6" : (0,0),
    }

    game = board.copy()
    for _ in red:
        game.paste(p1, tiles[_])
    for _ in yellow:
        game.paste(p2, tiles[_])

    game.save(f'Games/{game_id}.png')
    return f'Games/{game_id}.png'

def remove_expired():               # Deletes all expired games
    try:
        for game in database.child("Connect-4").get().each():
            expiry, id = int(game.val()["expiry"]), game.val()["id"]
            if int(time()) - expiry >= 600:
                database.child(id).remove()
                bot.edit_message_text(inline_message_id=id, text="<b>Game expired! 🙃</b>")
                bot.edit_message_reply_markup(inline_message_id=id, reply_markup=None)
    except:
        pass

def parse_board(red, yellow):           # Converts board image to ascii format

    board = [
        ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1'],
        ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2'],
        ['A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3'],
        ['A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4'],
        ['A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5'],
        ['A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6'],
    ]

    for __ in board:
        for _ in __:
            if _ in red:    __[__.index(_)] = 1
            elif _ in yellow:   __[__.index(_)] = 2
            else:   __[__.index(_)] = 0

    return board

def chk_win(board, piece, cols=7, rows=6):          # Checks if player has wons

	for c in range(cols-3):     # Horizonatal arrangement
		for r in range(rows):
			if board[r][c] == piece\
                and board[r][c+1] == piece\
                and board[r][c+2] == piece\
                and board[r][c+3] == piece:
				return True

	for c in range(cols):       # Vertical arrangement
		for r in range(rows-3):
			if board[r][c] == piece\
                and board[r+1][c] == piece\
                and board[r+2][c] == piece\
                and board[r+3][c] == piece:
				return True

	for c in range(cols-3):     # Positive Diagonals
		for r in range(rows-3):
			if board[r][c] == piece\
                and board[r+1][c+1] == piece\
                and board[r+2][c+2] == piece\
                and board[r+3][c+3] == piece:
				return True

	for c in range(cols-3):     # Negative Diagonals
		for r in range(3, rows):
			if board[r][c] == piece\
                and board[r-1][c+1] == piece\
                and board[r-2][c+2] == piece\
                and board[r-3][c+3] == piece:
				return True

@bot.message_handler(commands="start")
def start(message):                         # Starts the bot

    bot.send_photo(message.chat.id, BANNER, caption="<b>Wanna a play a game of Connect-4?\n\
    \nClick the buton and play with your friends!</b>",
    reply_markup = InlineKeyboardMarkup().row(InlineKeyboardButton("Play Connect-4!",
    switch_inline_query="connect_4")))

@bot.inline_handler(lambda query: len(query.query) == 0 or query.query == 'connect_4')
def send_game(query):                   # Creating the inline query handler

    try:
        c_4 = InlineQueryResultPhoto('_c4_',
        'https://raw.githubusercontent.com/TECH-SAVVY-GUY/telegram-games/master/assets/game_board.jpg',
        'https://raw.githubusercontent.com/TECH-SAVVY-GUY/telegram-games/master/assets/connect-4.jpg',
        title = "ᑕᗝᑎᑎᗴᑕ丅 - 4", description="Play a game of Connect-4 with your friends and family! ✌🏻",
        reply_markup = InlineKeyboardMarkup().row(InlineKeyboardButton("Tap to play!",
        callback_data=f"c-play{query.from_user.id}")), caption = "<b>Start the game! 🥳\n\
            \nGame will be expire in 10 minutes!</b>", parse_mode = "HTML"
        )
        bot.answer_inline_query(query.id, [c_4])
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):                        # A single callback listener for all calls

    data, game_id = call.data, call.inline_message_id
   
    if data[:6] == "c-play":                        # Starting the game
        
        red, yellow = int(data[6:]), int(call.from_user.id)

        if red == yellow:
            bot.answer_callback_query(call.id,
            "⚠️ Must be a different player! ⚠️", show_alert=True)
        else:
            database.child("Connect-4").child(game_id).child("id").set(game_id)
            database.child("Connect-4").child(game_id).child("red").set(int(data[6:]))
            database.child("Connect-4").child(game_id).child("yellow").set(call.from_user.id)
            database.child("Connect-4").child(game_id).child("count").set(1)
            database.child("Connect-4").child(game_id).child(
                "board").set("['A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6']")
            database.child("Connect-4").child(game_id).child("red_places").set("[]")
            database.child("Connect-4").child(game_id).child("yellow_places").set("[]")
            database.child("Connect-4").child(game_id).child("expiry").set(int(time()))

            bot.edit_message_caption(inline_message_id=game_id, caption=" ")
            bot.edit_message_reply_markup(inline_message_id=game_id,
            reply_markup=connect_4_markup("🔴", ["A6", "B6", "C6", "D6", "E6", "F6", "G6"]))

    else:       # Player move algorithm
            game = database.child("Connect-4").child(game_id).get()
            players = [int(game.val()["red"]), int(game.val()["yellow"])]
            
            if call.from_user.id not in players:
                bot.answer_callback_query(call.id,
                "❌  You are not a player!  ❌", show_alert=True)
            else: 
                count = int(game.val()["count"]) 
                if count % 2 != 0:
                    if call.from_user.id != players[0]:
                        bot.answer_callback_query(call.id,
                            "⚠️ Wait for your Turn! ⚠️", show_alert=True)
                    else:   
                        if data[1] != "0":                   
                            board = eval(game.val()["board"])
                            board[board.index(data)] = data[0] + str(int(data[1]) - 1)
                            database.child("Connect-4").child(game_id).update({"board":f"{board}"})
                            red_places, yellow_places = eval(game.val()["red_places"]), eval(game.val()["yellow_places"])
                            red_places.append(data)
                            parsed_board = parse_board(red_places, yellow_places)
                            if chk_win(parsed_board, 1):
                                database.child("Connect-4").child(game_id).remove()
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic)) 
                                bot.edit_message_caption(inline_message_id=game_id,
                                caption="<b><i>Player 🔴 wins! 🥳</i></b>")                                                                                                  
                                try: os.remove(path)  
                                except: pass  
                            elif board == ["A0", "B0", "C0", "D0", "E0", "F0", "G0"]:
                                database.child("Connect-4").child(game_id).remove()
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic))
                                bot.edit_message_caption(inline_message_id=game_id,
                                caption="<b><i>It's a draw! 🥱</i></b>")                                   
                            else:                               
                                database.child("Connect-4").child(game_id).update({"red_places":f"{red_places}"})
                                database.child("Connect-4").child(game_id).update({"count":count + 1})
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic)) 
                                    bot.edit_message_reply_markup(inline_message_id=game_id,
                                    reply_markup=connect_4_markup("🟡", board))                                   
                                try: os.remove(path)  
                                except: pass    
                else:
                    if call.from_user.id != players[-1]:
                        bot.answer_callback_query(call.id,
                            "⚠️ Wait for your Turn! ⚠️", show_alert=True)
                    else:   
                        if data[1] != "0":                   
                            board = eval(game.val()["board"])
                            board[board.index(data)] = data[0] + str(int(data[1]) - 1)
                            database.child("Connect-4").child(game_id).update({"board":f"{board}"})
                            red_places, yellow_places = eval(game.val()["red_places"]), eval(game.val()["yellow_places"])
                            yellow_places.append(data)
                            parsed_board = parse_board(red_places, yellow_places)
                            if chk_win(parsed_board, 2):
                                database.child("Connect-4").child(game_id).remove()
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic))
                                bot.edit_message_caption(inline_message_id=game_id,
                                caption="<b><i>Player 🟡 wins! 🥳</i></b>")                                                                                                  
                                try: os.remove(path)  
                                except: pass   
                            elif board == ["A0", "B0", "C0", "D0", "E0", "F0", "G0"]:
                                database.child("Connect-4").child(game_id).remove()
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic))
                                bot.edit_message_caption(inline_message_id=game_id,
                                caption="<b><i>It's a draw! 🥱</i></b>")                                
                            else:                                                                 
                                database.child("Connect-4").child(game_id).update({"yellow_places":f"{yellow_places}"})
                                database.child("Connect-4").child(game_id).update({"count":count + 1})
                                path = board_img(red_places, yellow_places, game_id)
                                with open(path, "rb") as pic:
                                    pic = bot.send_photo(STORAGE_CHANNEL, pic)
                                    pic = bot.get_file(pic.photo[-1].file_id).file_id
                                    bot.edit_message_media(inline_message_id=game_id, media=InputMediaPhoto(pic))                                
                                    bot.edit_message_reply_markup(inline_message_id=game_id,
                                    reply_markup=connect_4_markup("🔴", board))                              
                                try: os.remove(path)  
                                except: pass                      

def thrd():
    while True:
        schedule.run_pending()
        sleep(1)

schedule.every(1).minutes.do(remove_expired)
t = threading.Thread(target=thrd)     

def main():  
    t.start()      
    bot.infinity_polling()
