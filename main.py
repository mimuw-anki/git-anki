import glob
import hashlib
import os
import sys
from typing import List, Set, Union, Sequence

import genanki

from card_styles import BASE_MODEL

DEBUG = False
DUMMY_DECK_ID = 97925
PLACEHOLDER_DECK_NAME = "Test deck (mimuw-anki)"


class AnkiNoteGuidOfDeckIdAndCardId(genanki.Note):
    def __init__(self, *args, **kwargs):
        self.deck_id = kwargs.pop("deck_id")
        self.card_id = kwargs.pop("card_id")
        super().__init__(*args, **kwargs)

    @property
    def guid(self) -> int:
        return genanki.guid_for(self.deck_id, self.card_id)


class InputFile:
    def __init__(
        self, file_path: str, file_ids_store: Set[str], model: genanki.Model
    ) -> None:
        with open(file_path) as f:
            lines = [
                stripped_line for l in f.readlines() if (stripped_line := l.strip())
            ]

        deck_id, deck_name, f_id, *fishcards_lines = lines

        assert f_id.startswith("file_id:")
        file_id = f_id.lower().strip()
        if file_id in file_ids_store:
            raise ValueError(f"Duplicate file_id: {file_id}")
        file_ids_store.add(file_id)

        field_names = [f["name"] for f in model.fields.copy()]
        fields_per_fishcards = len(field_names) + 1  # + card_id

        if len(fishcards_lines) % fields_per_fishcards != 0:
            raise ValueError("Wrong file format")

        cards, card_ids = [], set()
        for i in range(0, len(fishcards_lines), fields_per_fishcards):
            card: dict[str, Union[str, int]] = {
                "card_id": self._hash((fishcards_lines[i], file_id))
            }
            if card["card_id"] in card_ids:
                raise ValueError(
                    f"Duplicate card id {card['card_id']} in file {file_id}"
                )
            card_ids.add(card["card_id"])

            card.update(zip(field_names, fishcards_lines[i + 1 :]))
            cards.append(card)

        self.deck_id = deck_id
        self.deck_name = deck_name
        self.cards = cards

    @staticmethod
    def _hash(string_sequence: Sequence[str]) -> str:
        sha256 = hashlib.sha256()
        for string in string_sequence:
            sha256.update(string.encode("utf-8"))
        return sha256.hexdigest()


class NoteGenerator:
    def __init__(self, model: genanki.Model, use_dummy_id: bool = False) -> None:
        self.cards: List[dict] = []
        self.model = model
        self.use_dummy_id = use_dummy_id
        self.deck_id = DUMMY_DECK_ID
        self.deck_name = PLACEHOLDER_DECK_NAME
        self._processed_file_ids: Set[str] = set()

    def make_note(self, item: dict) -> AnkiNoteGuidOfDeckIdAndCardId:
        assert self.use_dummy_id or self.deck_id != DUMMY_DECK_ID
        return AnkiNoteGuidOfDeckIdAndCardId(
            model=self.model,
            card_id=item["card_id"],
            fields=[item[field["name"]] for field in self.model.fields],
            deck_id=self.deck_id,
        )

    def update_deck_data(self, deck_id_raw: str, deck_name_raw: str) -> None:
        assert deck_id_raw.lower().startswith("deck_id:")
        assert deck_name_raw.lower().startswith("deck_name:")

        deck_id = int(deck_id_raw.split("deck_id:", 1)[1].strip())
        deck_name = deck_name_raw.split("deck_name:", 1)[1].strip()

        if self.use_dummy_id:
            # The lines above are executed unconditionally so that they verify
            # the validity of data & format.
            return

        if self.deck_id != DUMMY_DECK_ID:
            # It's not the first file.
            if self.deck_id != deck_id or self.deck_name != deck_name:
                raise ValueError("Ambiguous deck_id or deck_name")

        self.deck_id = deck_id
        self.deck_name = deck_name

    def process_file(self, file_path: str) -> None:
        # Create list of dicts, where each dict has all fields specified in self.model + id.
        file = InputFile(
            file_path, file_ids_store=self._processed_file_ids, model=self.model
        )
        self.update_deck_data(file.deck_id, file.deck_name)
        self.cards.extend(file.cards[::-1])  # needed to preserve the original order

    def export(self) -> None:
        deck = genanki.Deck(self.deck_id, self.deck_name)
        deck.add_model(self.model)

        for item in self.cards[::-1]:  # [::-1] needed to preserve the original order
            deck.add_note(self.make_note(item))

        my_package = genanki.Package(deck)
        my_package.write_to_file("deck.apkg")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Missing parameter: release/debug")
    if len(sys.argv) < 3:
        raise ValueError("Missing parameter: file path")
    path = sys.argv[2]

    if sys.argv[1].lower() == "debug":
        gen = NoteGenerator(BASE_MODEL, use_dummy_id=True)
        gen.process_file(path)
    else:
        gen = NoteGenerator(BASE_MODEL)
        os.chdir(path)
        filenames = glob.glob("./*.txt")
        for f in filenames:
            if DEBUG:
                print(f)
            gen.process_file(f)

    gen.export()
