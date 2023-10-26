import logging
import string

import pymorphy2
from typing import Any, Text, Dict, List

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.executor import CollectingDispatcher


class ValidateGameInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_form_game_info"

    async def extract_CURRENT_SCORE(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        names_list = tracker.get_slot('NAMES_LIST')

        if tracker.get_slot("requested_slot") != "NAMES_LIST" or names_list is None:
            return {}

        normalized_names = [normalize_name(name) for name in names_list]

        dispatcher.utter_message(text="Записал имена " + ", ".join(normalized_names))

        return {"CURRENT_SCORE": {name: 0 for name in normalized_names}}


    async def extract_MAX_SCORE(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        number = tracker.get_slot('MAX_SCORE')
        score = tracker.get_slot('CURRENT_SCORE')

        if tracker.get_slot("requested_slot") != "MAX_SCORE" or number is None:
            return {}
        score["Играем до"] = int(number)
        dispatcher.utter_message(text=f"Хорошо, будем играть до {number}")
        return {"CURRENT_SCORE": score}

    

class ActionShowScore(Action):

    def name(self) -> Text:
        return "action_show_score"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        score = get_current_score(tracker)

        if score is None or score==dict():
            dispatcher.utter_message(text="Вы еще не начали игру")
        else: 
            dispatcher.utter_message(text="Счет на текущий момент \n"+ "\n".join([f"{key}: {value}" for key, value in score.items()]))
        return []


class ActionRestartGame(Action):

    def name(self) -> Text:
        return "action_restart"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Окей, начал новую игру")

        return [
            SlotSet("GAME_TITLE", None),
            SlotSet("CURRENT_SCORE", None),
            SlotSet("NAMES_LIST", None),
            SlotSet("NAME", None),
            SlotSet("POINTS", None),
        ]


class ActionAddPoints(Action):

    def name(self) -> Text:
        return "action_add_points"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = normalize_name(str(tracker.get_slot('NAME')))
        points = int(tracker.get_slot('POINTS'))
        current_score = get_current_score(tracker)

        logging.info("ActionAddPoints: name: {0}, points: {1}, current_score: {2}".format(name, points, current_score))

        if not current_score.__contains__(name):
            dispatcher.utter_message(
                text="Не нашел игрока с именем {0} в таблице, добавить?".format(name),
                buttons=[
                    {"payload": "/add_unknown_player", "title": "Да"},
                    {"payload": "/okay", "title": "Нет"},
                ]
            )
            return []
        else:
            current_score[name] += points
            
        flag, msg, slots_val = is_game_over(tracker, current_score)
        if flag:
            dispatcher.utter_message(text=msg)
            return slots_val

        dispatcher.utter_message(text="Добавил {0} {1} игроку {2}".format(points, get_points_for_number(points), name))
        return [SlotSet("CURRENT_SCORE", current_score)]


class ActionRemovePoints(Action):

    def name(self) -> Text:
        return "action_remove_points"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = normalize_name(str(tracker.get_slot('NAME')))
        points = abs(int(tracker.get_slot('POINTS')))
        current_score = get_current_score(tracker)

        logging.info(
            "ActionRemovePoints: name: {0}, points: {1}, current_score: {2}".format(name, points, current_score))

        if not current_score.__contains__(name):
            dispatcher.utter_message(
                text="Не нашел игрока с именем {0} в таблице, добавить?".format(name),
                buttons=[
                    {"payload": "/add_unknown_player", "title": "Да"},
                    {"payload": "/okay", "title": "Нет"},
                ]
            )
            return []
        else:
            current_score[name] -= points

        dispatcher.utter_message(text="Снял {0} {1} игроку {2}".format(points, get_points_for_number(points), name))
        return [SlotSet("CURRENT_SCORE", current_score)]


class ActionAddUnknownPlayer(Action):

    def name(self) -> Text:
        return "action_add_unknown_player"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = normalize_name(str(tracker.get_slot('NAME')))
        points = int(tracker.get_slot('POINTS'))
        current_score = get_current_score(tracker)

        logging.info("ActionAddUnknownPlayer: name: {0}, current_score: {1}".format(name, current_score))

        if not current_score.__contains__(name):
            current_score[name] = points

        dispatcher.utter_message(
            text="Добавил игрока {0} с количеством {1} {2}".format(name, get_points_for_number(points), points))
        return [SlotSet("CURRENT_SCORE", current_score)]


morph = pymorphy2.MorphAnalyzer(lang='ru')


def normalize_name(name: string):
    return morph.parse(name)[0].normal_form.title()


def get_points_for_number(number: int):
    points = morph.parse('балл')[0]
    return points.make_agree_with_number(number).word


def get_current_score(tracker: Tracker):
    score = tracker.get_slot("CURRENT_SCORE")
    if score is None:
        return {}
    return dict(score)

def is_game_over(tracker: Tracker, score):
    max_score = tracker.get_slot("CURRENT_SCORE")["Играем до"]
    print(max_score)
    print(score)
    if max_score is None:
        return False, "", []
    
    for key, value in score.items():
        print(value>= max_score)
        if key!="Играем до" and value >= int(max_score):
            logging.info("is_game_over: True")
            msg = f"Поздравляю, игрок {key} победил! Игра окончена со счетом \n"
            for key, value in score.items():
                if key!="Играем до":
                    msg += f"{key}: {value} \n"
            return True, msg, [
                SlotSet("GAME_TITLE", None),
                SlotSet("CURRENT_SCORE", None),
                SlotSet("NAMES_LIST", None),
                SlotSet("NAME", None),
                SlotSet("POINTS", None),
                SlotSet("MAX_SCORE", None)
            ]
    logging.info("is_game_over: False")
    return False, "", []