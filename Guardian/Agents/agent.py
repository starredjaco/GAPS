import ExecutionEngine.chatgpt as chatgpt
from configs import *
import Infra.util as util
from Infra.hierarchy import (
    SemanticHierarchy,
    TotalVisibleHierarchy,
    VisibleHierarchy,
)
from ExecutionEngine.screen_control import AndroidController
from typing import List, Tuple, Callable
from Infra.infra import TestCase, EventSeq, Event, Widget
from Memory.context import Context
import re


class Agent:
    """
    Represents an LLM agent for Android UI testing.
    Attributes:
    - app (str): The name of the app under test.
    - target (str): The testing objective.
    - initial_prompt (str): The initial prompt for the conversation with the LLM.
    - first_prompt (str): The first prompt for the conversation with the LLM, including the app name and testing target.
    - targetPrompt (str): The prompt reminding the LLM of the testing objective.
    - session (chatgpt.Session): The chatGPT session for the conversation with the LLM.
    Methods:
    - __init__(self, _app, _pkg, _target: str): Initializes the Agent object.
    - act(self, events: List[Event]): Performs an action based on the given events.
    - obtain_event_to_execute(self, events: List[Event]): Obtains the event to execute based on the given events.
    - getInput(self, target) -> str: Asks chatGPT for the text input.
    """

    def __init__(self, app_name, target: str):
        self.app_name = app_name
        self.testing_objective = target
        self.initial_prompt = (
            f"You are an expert in Android UI testing assisting with automated interaction for the {self.app_name} app. "
            "Our goal is to reach a specific testing target by exploring the app's interface. "
            "In each interaction round, I will provide a list of UI elements currently visible on the screen. "
            "Your task is to select exactly one UI element (by its index) that is most likely to lead us closer to the target. \n"
        )

        self.exploration_strategy = (
            'Prioritize UI elements that involve text input, confirm current actions (such as buttons labeled "OK" or "Confirm"), or advance the flow forward through the app. '
            "Avoid selecting elements that trigger back navigation, cancel actions, or lead away from progress, unless absolutely necessary. "
            "Always aim to move forward through the app's interface toward the goal.\n"
        )

        self.first_prompt = (
            self.initial_prompt
            + self.exploration_strategy
            + f"We are testing the {self.app_name} app . "
            + f"Our testing target is to {self.testing_objective}."
        )

        self.targetPrompt = f"Remember our test target is to {self.testing_objective} on {self.app_name}."
        chatgpt.setupChatGPT(self.first_prompt)
        self.session = None
        # self.session = chatgpt.Session()

    def plan(self, events: List[Event], activity, activity_history):
        event = self.obtain_event_to_execute(
            events, activity, activity_history
        )
        if event is None:
            return None
        if event.action == "text":
            event.input = self.getInput(
                self.testing_objective, event.widget.contentDesc
            )
        return event

    def obtain_event_to_execute(
        self, events: List[Event], current_activity, activity_history
    ):
        # remove previous actions performed in the same activity
        if len(events) > 1:
            for action_widget in activity_history:
                for event in events:
                    splits = action_widget.split()
                    if len(splits) > 2:
                        action, widget = splits[:2]
                    elif len(splits) == 2:
                        action, widget = splits
                    else:
                        widget = action = splits
                    # print(activity, action, widget)
                    if (
                        f"{action}" == event.action
                        and f"{widget}"
                        == event.widget.resourceId.split("/")[-1]
                    ):
                        events.remove(event)

        if len(events) == 0:
            if len(activity_history) > 0:
                activity_history.pop(0)

        filteredEvents = list(
            filter(
                lambda x: x[1].strip() != "a View () to click",
                [(i, e.dump()) for i, e in enumerate(events)],
            )
        )

        elemDesc = [f"index-{i}: {x[1]}" for i, x in enumerate(filteredEvents)]
        event_map = {i: e[0] for i, e in enumerate(filteredEvents)}

        description = (
            f'Currently we are in a screen named "{current_activity}" and we have {len(elemDesc)} widgets, namely:\n'
            + "\n".join(elemDesc)
        )

        task = self.targetPrompt
        prompt = "\n".join([description, self.exploration_strategy, task])
        self.session = chatgpt.Session()
        # print(prompt)
        idx = self.session.queryIndex(
            prompt, lambda x: x in range(len(events))
        )
        # print(idx)
        if idx == -1:
            for action in activity_history:
                if "text" == action.split()[0]:
                    return None
            return Event.back()
        return events[event_map[idx]]

    def getInput(self, target, text) -> str:
        # ask chatGPT what text to input
        task = (
            "You have selected a TextEdit view, which requires a text input."
            'Never answer with "none" or invalid input.'
            f"Remember that your task is to {target}"
        )
        requirement = (
            "Please insert the text that you want to input."
            "Please only respond with the text input and nothing else."
        )
        if text.strip():
            task += f'\nInsert the text accordingly, considering that the description of the input field is: "{text}"'
        return self.session.queryString(f"{task}\n{requirement}")
