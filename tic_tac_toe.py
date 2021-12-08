import telebot
import pyrebase
import threading
import schedule
from time import time, sleep
from tabulate import tabulate
from telebot.types import InlineKeyboardButton
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineQueryResultArticle
from telebot.types import InputTextMessageContent

config = {

    "apiKey"              : "",
    "authDomain"          : "",
    "databaseURL"         : "",
    "projectId"           : "",
    "storageBucket"       : "",
    "messagingSenderId"   : "",
    "appId"               : "",
    "measurementId"       : "",  
}                                   # Your FIREBASE DATABASE configurations

def emoji_board(game):              # Creates the board in ASCII format
    emojis = {"-":"-", "x":"x","o":"o"}
    board, temp = [], []
    for count, _ in enumerate(game, 1):
        if count == len(game):
            temp.append(emojis[_])
            board.append(temp)
        elif count % 3 != 0:
            temp.append(emojis[_])
        else:
            temp.append(emojis[_])
            board.append(temp)
            temp = []

    return tabulate(board, tablefmt="grid")

def check_win(game, game_id):       # Checks the status of the game  

    wins = [
        (0,1,2), (3,4,5), (6,7,8), (0,4,8),
        (0,3,6), (1,4,7), (2,5,8), (2,4,6),
    ]
    
    for win in wins:

        C1 = (game[win[0]], game[win[1]], game[win[2]]) == ("x","x","x")
        C2 = (game[win[0]], game[win[1]], game[win[2]]) == ("o","o","o")

        if C1 or C2:
            bot.edit_message_reply_markup(inline_message_id=game_id, reply_markup=None)
            winner = "X" if C1 else "O"
            bot.edit_message_text(inline_message_id=game_id, text=f"<b>Congratulations! 🎉\n\
            \nPlayer {winner} wins! 🥳\n\n<code>{emoji_board(game)}</code></b>")
            database.child(game_id).remove()
            return "True"
    else:
        if "-" not in game: return "Draw"
        else:   return "False"

firebase = pyrebase.initialize_app(config)
database = firebase.database()

API_KEY = ""    # API TOKEN from @BotFather
BANNER  = ""    # FILE ID of banner for your bot

bot = telebot.TeleBot(API_KEY, parse_mode="HTML")   # Initializing the bot

def remove_expired():   # Deletes all expired games
    try:
        for game in database.get().each():
            expiry, id = int(game.val()["expiry"]), game.val()["id"]
            if int(time()) - expiry >= 300:
                database.child(id).remove()
                bot.edit_message_text(inline_message_id=id, text="<b>Game expired! 🙃</b>")
                bot.edit_message_reply_markup(inline_message_id=id, reply_markup=None)
    except:
        pass

def create_game_board(game):    # Creates a new empty game board

    game_board, buttons = InlineKeyboardMarkup(row_width = 3), []

    for pos, _ in enumerate(game, 1):
        buttons.append(InlineKeyboardButton(_, callback_data=f'{pos}'))
    game_board.add(*buttons)

    return game_board

@bot.message_handler(commands="start")
def start(message):                     # Starts the bot

    bot.send_photo(message.chat.id, BANNER, caption="<b>Wanna a play a game of Tic-Tac-Toe?\n\
    \nClick the buton and play with your friends!</b>",
    reply_markup = InlineKeyboardMarkup().row(InlineKeyboardButton("Play Tic-Tac-Toe!",
    switch_inline_query="tic_tac_toe")))

@bot.inline_handler(lambda query: len(query.query) == 0 or query.query == 'tic_tac_toe')   
def send_game(query):       # Creating the inline query handler

    play = InlineKeyboardMarkup().row(InlineKeyboardButton("Tap to play!",
    callback_data=f"play{query.from_user.id}"))

    try:
        t_t_t = InlineQueryResultArticle('start_game',"丅Ꭵᑕ-丅ᗩᑕ-丅ᗝᗴ",
        InputTextMessageContent("<b>Start the game! 🥳\n\nGame will be expire in 5 minutes!</b>",
        parse_mode = "HTML"),reply_markup = play,
        description = "Play a game of Tic-Tac-Toe with your friends and family! ✌🏻",
        thumb_url = "https://github.com/TECH-SAVVY-GUY/TELEGRAM-BOTS/blob/master/assets/tic-tac-toe.png?raw=true")
        bot.answer_inline_query(query.id, [t_t_t])
    except:
        pass

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):                        # A single callback listener for all calls

    data, game_id = call.data, call.inline_message_id
   
    if data[:4] == "play":              # Starting the game
        
        player_x, player_o = int(data[4:]), int(call.from_user.id)

        if player_o == player_x:
            bot.answer_callback_query(call.id,
            "⚠️ Must be a different player! ⚠️", show_alert=True)
        else:
            bot.edit_message_text(inline_message_id=game_id, text="<b>Game in progress!</b>")
            bot.edit_message_reply_markup(inline_message_id=game_id,
            reply_markup=create_game_board(["-"] * 9))

            database.child(game_id).child("id").set(game_id)
            database.child(game_id).child("player_x").set(int(data[4:]))
            database.child(game_id).child("player_o").set(call.from_user.id)
            database.child(game_id).child("count").set(1)
            database.child(game_id).child("board").set(f"{['-'] * 9}")
            database.child(game_id).child("expiry").set(int(time()))

    elif data.isnumeric():      # Player move algorithm

        if int(data) in range(1,10):

            game = database.child(game_id).get()
            players = [int(game.val()["player_x"]), int(game.val()["player_o"])]
            
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
                        board = eval(game.val()["board"])
                        if board[int(data)-1] == "-":
                            board[int(data)-1] = "x"
                            bot.edit_message_reply_markup(inline_message_id=game_id,
                            reply_markup=create_game_board(board))    
                            stat = check_win(board, game_id)
                            if stat != "True":
                                if str(stat) == "Draw":
                                    bot.edit_message_reply_markup(inline_message_id=game_id, reply_markup=None)
                                    bot.edit_message_text(inline_message_id=game_id,
                                    text = f"<b>It's a draw! 🥱\n\n<code>{emoji_board(board)}</code></b>")
                                    database.child(game_id).remove()                             
                                else:
                                    database.child(game_id).update({"board":str(board)})
                                    database.child(game_id).update({"count":count + 1})  

                else:
                    if call.from_user.id != players[-1]:
                        bot.answer_callback_query(call.id,
                            "⚠️ Wait for your Turn! ⚠️", show_alert=True)
                    else:
                        board = eval(game.val()["board"])
                        if board[int(data)-1] == "-": 
                            board[int(data)-1] = "o"
                            bot.edit_message_reply_markup(inline_message_id=game_id,
                            reply_markup=create_game_board(board))    
                            stat = check_win(board, game_id)
                            if stat != "True":
                                if str(stat) == "Draw":
                                    bot.edit_message_reply_markup(inline_message_id=game_id, reply_markup=None)
                                    bot.edit_message_text(inline_message_id=game_id,
                                    text = f"<b>It's a draw! 🥱\n\n<code>{emoji_board(board)}</code></b>")  
                                    database.child(game_id).remove()                                                               
                                else:
                                    database.child(game_id).update({"board":str(board)})
                                    database.child(game_id).update({"count":count + 1})                                   

def thrd():         # Scheduling the deletion of expired games
    while True:
        schedule.run_pending()
        sleep(1)

schedule.every(1).minutes.do(remove_expired)
t = threading.Thread(target=thrd)               # Creating a seperate thread

def main():     # Executing all the threads
    t.start()      
    bot.infinity_polling()
