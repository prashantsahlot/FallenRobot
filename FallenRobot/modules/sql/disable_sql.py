import threading
from sqlalchemy import Column, String, UnicodeText, distinct, func
from FallenRobot.modules.sql import BASE, SESSION


class Disable(BASE):
    __tablename__ = "disabled_commands"
    chat_id = Column(String(14), primary_key=True, nullable=False)
    command = Column(String(255), primary_key=True, nullable=False)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command

    def __repr__(self):
        return f"Disabled cmd {self.command} in {self.chat_id}"


DISABLE_INSERTION_LOCK = threading.RLock()
DISABLED = {}


def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        try:
            disabled = SESSION.query(Disable).filter_by(chat_id=str(chat_id), command=disable).first()

            if not disabled:
                DISABLED.setdefault(str(chat_id), set()).add(disable)
                new_disable = Disable(chat_id=str(chat_id), command=disable)
                SESSION.add(new_disable)
                SESSION.commit()
                return True
            return False
        except Exception as e:
            SESSION.rollback()
            raise e
        finally:
            SESSION.close()


def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        try:
            disabled = SESSION.query(Disable).filter_by(chat_id=str(chat_id), command=enable).first()

            if disabled:
                DISABLED.get(str(chat_id), set()).discard(enable)
                SESSION.delete(disabled)
                SESSION.commit()
                return True
            return False
        except Exception as e:
            SESSION.rollback()
            raise e
        finally:
            SESSION.close()


def is_command_disabled(chat_id, cmd):
    return str(cmd).lower() in DISABLED.get(str(chat_id), set())


def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())


def num_chats():
    try:
        return SESSION.query(func.count(distinct(Disable.chat_id))).scalar()
    except Exception as e:
        SESSION.rollback()
        raise e
    finally:
        SESSION.close()


def num_disabled():
    try:
        return SESSION.query(Disable).count()
    except Exception as e:
        SESSION.rollback()
        raise e
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        try:
            chats = SESSION.query(Disable).filter_by(chat_id=str(old_chat_id)).all()
            for chat in chats:
                chat.chat_id = str(new_chat_id)
                SESSION.add(chat)

            if str(old_chat_id) in DISABLED:
                DISABLED[str(new_chat_id)] = DISABLED.pop(str(old_chat_id), set())

            SESSION.commit()
        except Exception as e:
            SESSION.rollback()
            raise e
        finally:
            SESSION.close()


def __load_disabled_commands():
    global DISABLED
    try:
        Disable.__table__.create(bind=SESSION.get_bind(), checkfirst=True)  # Ensure table creation
        all_chats = SESSION.query(Disable).all()
        for chat in all_chats:
            DISABLED.setdefault(chat.chat_id, set()).add(chat.command)
    except Exception as e:
        SESSION.rollback()
        raise e
    finally:
        SESSION.close()


# Initialize disabled commands on load
__load_disabled_commands()
