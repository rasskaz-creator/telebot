import sqlalchemy as sq
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DSN

Base = declarative_base()

engine = sq.create_engine(DSN)

Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'

    id = sq.Column(sq.Integer, primary_key=True)
    user_name = sq.Column(sq.String(length=40), unique=True)
    telegram_id = sq.Column(sq.Integer, unique=True)

class Words(Base):
    __tablename__ = 'words'

    id = sq.Column(sq.Integer, primary_key=True)
    word = sq.Column(sq.Text, nullable=False)
    translation = sq.Column(sq.Text, nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.telegram_id"), nullable=False)

    user = relationship(User, backref="words")


class Global_Words(Base):
    __tablename__ = 'global_words'
    
    id = sq.Column(sq.Integer, primary_key=True)
    global_word = sq.Column(sq.Text, nullable=False, unique=True)
    translation = sq.Column(sq.Text, nullable=False)


def add_initial_global_words():
    initial_words = [
        {"global_word": "Привет", "translation": "Hi"},
        {"global_word": "Мир", "translation": "Peace"},
        {"global_word": "Яблоко", "translation": "Apple"},
        {"global_word": "Вода", "translation": "Water"},
        {"global_word": "Пока", "translation": "Bye"},
        {"global_word": "Кошка", "translation": "Cat"},
        {"global_word": "Собака", "translation": "Dog"},
        {"global_word": "Корова", "translation": "Cow"},
        {"global_word": "Машина", "translation": "Car"},
        {"global_word": "Ручка", "translation": "Pen"}
        ]

    with Session() as session: # Используем контекстный менеджер для сессии
        for word_data in initial_words:
            word = Global_Words(global_word=word_data['global_word'], translation=word_data['translation'])
            session.add(word)
        try:
            session.commit()  # Коммит изменений после добавления всех слов
            print("Все слова успешно добавлены.")
        except Exception as e:
            session.rollback()  # Откатить изменения в случае ошибки
            print(f"Ошибка при добавлении слов: {e}")

def create_db(): # создание таблиц
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def add_user(user_name, telegram_id):
    with Session() as session:  
        new_user = User(user_name=user_name, telegram_id=telegram_id)
        session.add(new_user)
        session.commit()
        
        
def delete_word(word_to_delete, user_id):
    with Session() as session:
        
        # Проверяем тип word_to_delete
        if isinstance(word_to_delete, Words):
            word_value = word_to_delete.word  # Получаем слово из объекта
        else:
            word_value = word_to_delete

        word = session.query(Words).filter_by(word=word_value, user_id=user_id).first()  # Найти слово в базе данных
        if word:
            session.delete(word)
            print(f'Слово "{word_value}" успешно удалено.')
        else:
            print(f'Слово "{word_value}" не найдено в базе данных.')

        session.commit()

def add_new_word(word, translation, user_id):
    with Session() as session:
        try:
            user = session.query(User).filter_by(telegram_id=user_id).one()  # Проверяем, существует ли пользователь
            new_word = Words(word=word, translation=translation, user_id=user_id)
            session.add(new_word)
            session.commit()
        except NoResultFound:
            print(f"Пользователь с ID {user_id} не найден в базе данных.")
        except Exception as e:
            session.rollback()
            print(f"Ошибка при добавлении слова: {e}")


def get_all_words_for_user(user_id):
    with Session() as session:
        global_words = session.query(Global_Words).all() # получаем общие слова для всех
        user_words = session.query(Words).filter(Words.user_id == user_id).all() # Получаем все слова, связанные с конкретным пользователем
        all_words = global_words + user_words
    return all_words
        

