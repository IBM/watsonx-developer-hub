import textwrap
import json
from collections.abc import Generator
from typing import Callable


class InteractiveChat:
    def __init__(
        self,
        ai_service_invoke: Callable,
        questions: tuple[str] = None,
        stream: bool = False,
        verbose: bool = True,
    ) -> None:
        self.ai_service_invoke = ai_service_invoke
        self._ordered_list = lambda seq_: "\n".join(
            f"\t{i}) {k}" for i, k in enumerate(seq_, 1)
        )
        self._delta_start = False
        self.verbose = verbose
        self.stream = stream

        self.questions = ("Hi! How are you?",) if questions is None else questions

        self._help_message = textwrap.dedent(
            """
        The following commands are supported:
          --> help | h : prints this help message
          --> quit | q : exits the prompt and ends the program
          --> list_questions : prints a list of available questions
        """
        )

    @property
    def questions(self) -> tuple:
        return self._questions

    @questions.setter
    def questions(self, q: tuple) -> None:
        self._questions = q
        self._questions_prompt = (
            f"\tQuestions:\n{self._ordered_list(self._questions)}\n"
        )

    def _user_input_loop(self) -> Generator[tuple[str, str], None, None]:
        print(self._help_message)

        while True:
            q = input("\nChoose a question or ask one of your own.\n --> ")

            _ = yield q, "question"

    def _print_message(self, message: dict) -> None:
        header = f" {message['role'].capitalize()} Message ".center(80, "=")
        if delta := message.get("delta"):
            if not self._delta_start:
                print("\n", header)
                self._delta_start = True
            print(delta, flush=True, end="")
        else:
            print("\n", header)
            print(f"{message.get('content', message)}")

    def run(self) -> None:
        # TODO implement signal handling (especially Ctrl-C)
        while True:
            try:
                q = None

                user_loop = self._user_input_loop()

                for action, stage in user_loop:  # unsupported command support!

                    if action == "h" or action == "help":
                        print(self._help_message)
                    elif action == "quit" or action == "q":
                        raise EOFError

                    elif action == "list_questions":
                        print(self._questions_prompt)

                    elif stage == "question":
                        user_message = {}
                        # small caveat -- if user answers to the chat a single digit we'll treat it as trying to choose on of our self.questions
                        if not action.isdigit():  # user defined question
                            user_message["content"] = action.strip()
                        else:
                            number = int(action)

                            print(f"you chose QUESTION {number}\n")
                            if number > len(self.questions) or number < 0:
                                print(
                                    "provided numbers have to match the available numbers"
                                )
                            else:
                                user_message["content"] = self.questions[number - 1]

                        request_payload_json = {
                            "messages": [{"role": "user", **user_message}]
                        }

                        resp = self.ai_service_invoke(request_payload_json)

                        if self.stream:
                            for r in resp:
                                if type(r) == str:
                                    r = json.loads(r)
                                for c in r["choices"]:
                                    self._print_message(c["message"])
                            self._delta_start = False
                        else:
                            resp_choices = resp.get("body", resp)["choices"]
                            choices = (
                                resp_choices if self.verbose else resp_choices[-1:]
                            )

                            for c in choices:
                                self._print_message(c["message"])

            except EOFError:
                break
