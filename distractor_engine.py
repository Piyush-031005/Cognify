import random


# =========================
# DISTRACTOR ENGINE
# =========================

def generate_options(concept_data):

    correct = concept_data["correct"]

    confusions = concept_data["confusions"]

    # combine
    all_options = [correct] + confusions

    # shuffle
    random.shuffle(all_options)

    # locate correct answer
    correct_index = all_options.index(correct)

    return {
        "options": all_options,
        "correct_index": correct_index
    }


# =========================
# APPLICATION OPTIONS
# =========================

def generate_application_options(concept_data):

    correct = random.choice(
        concept_data["applications"]
    )

    wrong = concept_data["confusions"][:]

    options = [correct] + wrong

    random.shuffle(options)

    correct_index = options.index(correct)

    return {
        "options": options,
        "correct_index": correct_index
    }


# =========================
# REASONING OPTIONS
# =========================

def generate_reasoning_options(concept_data):

    correct = random.choice(
        concept_data["reasoning"]
    )

    wrong = concept_data["confusions"][:]

    options = [correct] + wrong

    random.shuffle(options)

    correct_index = options.index(correct)

    return {
        "options": options,
        "correct_index": correct_index
    }