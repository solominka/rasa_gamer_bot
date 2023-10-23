import logging
import string

import pymorphy2
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction


class ActionSetNames(Action):

    def name(self) -> Text:
        return "action_set_names"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        names_list = tracker.get_slot('NAMES_LIST')
        normalized_names = [normalize_name(name) for name in names_list]

        dispatcher.utter_message(text="Записал имена " + ", ".join(normalized_names))

        return [SlotSet("CURRENT_SCORE", {name: 0 for name in normalized_names})]


class ActionAddPoints(Action):

    def name(self) -> Text:
        return "action_add_points"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        name = normalize_name(str(tracker.get_slot('NAME')))
        points = abs(int(tracker.get_slot('POINTS')))
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

        logging.info("ActionRemovePoints: name: {0}, points: {1}, current_score: {2}".format(name, points, current_score))

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
    # return morph.parse(name)[0].inflect('nomn').word


def get_points_for_number(number: int):
    points = morph.parse('балл')[0]
    return points.make_agree_with_number(number).word


def get_current_score(tracker: Tracker):
    score = tracker.get_slot("CURRENT_SCORE")
    if score is None:
        return {}
    return dict(score)
