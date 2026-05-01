question_sessions = []
reflection_text = ""


def add_question_session(obj):
    question_sessions.append(obj)


def get_all_sessions():
    return question_sessions


def set_reflection(text):
    global reflection_text
    reflection_text = text


def get_reflection():
    return reflection_text


def reset_results():
    global question_sessions, reflection_text
    question_sessions = []
    reflection_text = ""