import telebot
import random
from telebot import types # для реализации кнопочек
from telebot.handler_backends import State, StatesGroup # реализация состояний
from database import User, add_user, Session, delete_word, add_new_word, get_all_words_for_user, Global_Words, create_db, add_initial_global_words
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

user_word_data = {}

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    YES = 'Да'
    NO = 'Нет'
    CANCEL = 'Отмена'
    CONFIRM = 'Подтвердить'
    CONTINUE = 'Перейти к изучению слов'
    LIST_WORDS = 'Список всех слов'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.username  # Получаем имя пользователя
    telegram_id = message.from_user.id  # Получаем ID пользователя

    # Добавляем пользователя в базу данных, если его там нет
    with Session() as session:
        existing_user = session.query(User).filter_by(telegram_id=telegram_id).first() # Проверяем, есть ли пользователь в базе данных

    if not existing_user:
        add_user(user_name, telegram_id)  # Функция для добавления пользователя


    markup = types.ReplyKeyboardMarkup(row_width=2)  # реализация кнопочек (размер 2)

    yes_btn = types.KeyboardButton(Command.YES)
    no_btn = types.KeyboardButton(Command.NO)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)

    markup.add(yes_btn, no_btn, add_word_btn)

    bot.send_message(message.chat.id, f'Привет 👋 Давай попрактикуемся в английском языке.\nТренировки можешь проходить в удобном для себя темпе.\n'
                                      f'У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.\n'
                                      f'Для этого воспользуйся инструментами: \nдобавить слово ➕ \nудалить слово 🔙. \nНу что, начнём ⬇️', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == Command.YES or message.text == Command.NO)
def yes_or_no(message):
    # message.from_user.id и message.chat.id — это уникальные идентификаторы пользователя и чата, которые позволяют сохранить и получить персональные данные для каждого пользователя и чата.
    if message.text == Command.NO:
        bot.send_message(message.chat.id, 'Хорошо, мы можем позаниматься позже!')
    else:
        start_bot(message)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_the_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if 'target_word' in data:
            word_to_delete = data['target_word'] # Получаем слово, которое будет удалено
            markup = types.ReplyKeyboardMarkup(row_width=2)
            confirm_btn = types.KeyboardButton(Command.CONFIRM)
            cancel_btn = types.KeyboardButton(Command.CANCEL)
            markup.add(confirm_btn, cancel_btn)
            data['deleting_word'] = word_to_delete # Сохраняем состояние в data
            bot.send_message(message.chat.id, f'Ты точно хочешь удалить слово "{word_to_delete}"?', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Нет слова для удаления.')
        
        
@bot.message_handler(func=lambda message: message.text == Command.CONFIRM or message.text == Command.CANCEL)
def handle_confirmation(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if message.text == Command.CONFIRM:
            if 'deleting_word' in data:  # Проверяем, есть ли слово для удаления
                word_to_delete = data['deleting_word']
                print(isinstance(word_to_delete, Global_Words))
                if isinstance(word_to_delete, Global_Words): # Проверяем тип выбранного слова
                    word_value = word_to_delete.global_word  # Получаем слово из объекта
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    yes_btn = types.KeyboardButton(Command.YES)
                    no_btn = types.KeyboardButton(Command.NO)
                    markup.add(yes_btn, no_btn)
                    return bot.send_message(message.chat.id, f'Выбранное слово "{word_value}" не может быть удалено, так как это базовое слово бота. Удалять можно только добавленные самостоятельно слова. Вернуться к обучению слов?', reply_markup=markup)
                else:
                    delete_word(word_to_delete, message.from_user.id)  # Удаляем слово из БД
                    bot.send_message(message.chat.id, f'Слово "{word_to_delete}" удалено.')
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Уменьшаем клавиатуру по размеру
                    next_btn = types.KeyboardButton(Command.NEXT)
                    markup.add(next_btn)
                    bot.send_message(message.chat.id, 'Вы можете продолжить, нажав кнопку ниже:', reply_markup=markup)
                    del data['deleting_word']  # Удаляем ключ после использования
            else:
                bot.send_message(message.chat.id, 'Ошибка: Нет слова для удаления.')
            
        elif message.text == Command.CANCEL:
            bot.send_message(message.chat.id, 'Удаление слова отменено.')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Уменьшаем клавиатуру по размеру
            next_btn = types.KeyboardButton(Command.NEXT)
            markup.add(next_btn)
            bot.send_message(message.chat.id, 'Вы можете продолжить, нажав кнопку ниже:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == Command.LIST_WORDS)
def show_words(message):
    user_id = message.from_user.id
    all_words_for_user = get_all_words_for_user(user_id)
    words_list = '\n'.join([
        f'{i + 1}. {word.global_word if isinstance(word, Global_Words) else word.word} - {word.translation}'
        for i, word in enumerate(all_words_for_user)
    ])
    bot.send_message(message.chat.id, f'Список всех твоих слов для изучения:\n{words_list}')



@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def skip_word(message):
    start_bot(message)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    bot.send_message(message.chat.id, 'Введи слово на русском:', reply_markup=types.ReplyKeyboardRemove())
    user_word_data[message.from_user.id] = {'word': None, 'translation': None} # Инициализируем временное хранилище для пользователя

@bot.message_handler(func=lambda message: message.from_user.id in user_word_data and user_word_data[message.from_user.id]['word'] is None)
def translation_word(message):
    user_word_data[message.from_user.id]['word'] = message.text.strip()  # Сохраняем слово, убирая лишние пробелы
    bot.send_message(message.chat.id, 'Введи перевод этого слова:')
    
@bot.message_handler(func=lambda message: message.from_user.id in user_word_data and user_word_data[message.from_user.id]['word'] is not None and user_word_data[message.from_user.id]['translation'] is None)
def receive_translation(message):
    translation = message.text.strip()

    user_word_data[message.from_user.id]['translation'] = translation # Получаем перевод и сохраняем в хранилище
    word = user_word_data[message.from_user.id]['word']
    user_id = message.from_user.id

    add_new_word(word, translation, user_id) # Добавляем новое слово и его перевод в базу данных
    bot.send_message(message.chat.id, f'Слово "{word}" с переводом "{translation}" добавлено!')

    del user_word_data[message.from_user.id]  # Очищаем временное хранилище для пользователя

    words_count = len(get_all_words_for_user(user_id)) # Вывести количество изучаемых слов
    bot.send_message(message.chat.id, f'Ты изучаешь уже "{words_count}" слов(а)!')

    markup = types.ReplyKeyboardMarkup(row_width=2)  # реализация кнопочек
    continue_btn = types.KeyboardButton(Command.CONTINUE)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    markup.add(continue_btn, add_word_btn)
    bot.send_message(message.chat.id, 'Ты хочешь добавить новое слово или перейти к изучению слов?', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == Command.CONTINUE)
def command_continue(message):
        start_bot(message)
    

@bot.message_handler(commands=['cards'])
def start_bot(message):
    user_id = message.from_user.id
    words = get_all_words_for_user(user_id)

    if not words:
        bot.send_message(message.chat.id, "У вас еще нет добавленных слов. Добавьте слова.")
        return

    chosen_word = random.choice(words)
    
    if isinstance(chosen_word, Global_Words): # Проверяем тип выбранного слова
        target_word = chosen_word.global_word  # Используем global_word
        russian_word = chosen_word.translation
    else:
        target_word = chosen_word.word  # Используем word из таблицы Words
        russian_word = chosen_word.translation  # Перевод на русский
        
    other_words = [w.global_word if isinstance(w, Global_Words) else w.word for w in words if w != chosen_word]
    other_words = random.sample(other_words, min(len(other_words), 3))
    

    # Создаем и перемешиваем кнопки
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons = [types.KeyboardButton(word) for word in [target_word] + other_words]
    random.shuffle(buttons)
    markup.add(*buttons)

    # Дополнительные кнопки
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    list_btn = types.KeyboardButton(Command.LIST_WORDS)
    markup.add(next_btn, add_word_btn, delete_word_btn, list_btn)

    bot.send_message(message.chat.id, f'Какой перевод у слова {russian_word}?', reply_markup=markup)

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = russian_word
        data['other_words'] = other_words


@bot.message_handler(func=lambda message: True, content_types=['text']) # обрабатывай любой текст
def message_reply(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data: # bot.retrieve_data() — это метод для извлечения данных, которые были сохранены ранее
        # message.from_user.id и message.chat.id — это уникальные идентификаторы пользователя и чата, которые позволяют сохранить и получить персональные данные для каждого пользователя и чата.
        if 'target_word' in data:
            target_word = data['target_word']
            print("Полученное слово:", target_word)
            if message.text == target_word:
                bot.send_message(message.chat.id, 'Молодец! Нажми "дальше" для нового слова')
            else:
                bot.send_message(message.chat.id, 'Попробуй снова или нажми "дальше", чтобы сменить слово')
        else:
            bot.send_message(message.chat.id, 'Ошибка: нет установленного слова для угадывания.')



if __name__ == '__main__':
    create_db()
    add_initial_global_words()
    print('Bot is running!')
    bot.polling()
