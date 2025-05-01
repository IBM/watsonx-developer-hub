import textwrap
import json
from collections.abc import Generator
from typing import Callable


class InteractiveChat:
    def __init__(
        self,
        ai_service_invoke: Callable,
        locations: tuple[str] = None,
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

        self.locations = ("Saint-Tropez",) if locations is None else locations

        self._help_message = textwrap.dedent(
            """
        The following commands are supported:
          --> help | h : prints this help message
          --> quit | q : exits the prompt and ends the program
          --> list_locations : prints a list of available locations to plan travel today
        """
        )

    @property
    def locations(self) -> tuple:
        return self._locations

    @locations.setter
    def locations(self, q: tuple) -> None:
        self._locations = q
        self._locations_prompt = (
            f"\tLocations:\n{self._ordered_list(self._locations)}\n"
        )

    def _user_input_loop(self) -> Generator[tuple[str, str], None, None]:
        print(self._help_message)

        while True:
            q = input("\nChoose a location or submit one of your own.\n --> ")

            _ = yield q, "location"

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

                    elif action == "list_locations":
                        print(self._locations_prompt)

                    elif stage == "location":
                        user_message = {}
                        # small caveat -- if user answers to the chat a single digit we'll treat it as trying to choose on of our self.locations
                        if not action.isdigit():  # user defined location
                            user_message["content"] = action.strip()
                        else:
                            number = int(action)

                            print(f"you chose LOCATION {number}\n")
                            if number > len(self.locations) or number < 0:
                                print(
                                    "provided numbers have to match the available numbers"
                                )
                            else:
                                user_message["content"] = self.locations[number - 1]

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
