import glob
import os
import sys
from typing import List, TextIO

import genanki

from card_styles import BASE_MODEL
from config import DECK_ID, DECK_NAME

DEBUG = False


class AnkiNoteGuidOfIdAndKey(genanki.Note):
    def __init__(self, *args, **kwargs):
        self.deck_id = kwargs.pop('deck_id')
        self.card_id = kwargs.pop('card_id')
        super().__init__(*args, **kwargs)

    @property
    def guid(self) -> int:
        return genanki.guid_for(self.deck_id, self.card_id)


def nonblank_lines(file: TextIO):
    for line in file:
        new_line = line.rstrip()
        if new_line:
            yield new_line


class NoteGenerator:
    def __init__(self, model: genanki.Model, deck_id: int):
        self.cards: List[dict] = []
        self.model = model
        self.deck_id = deck_id

    def make_note(self, item: dict) -> AnkiNoteGuidOfIdAndKey:
        return AnkiNoteGuidOfIdAndKey(
            model=self.model,
            card_id=item['id'],
            fields=list(map(lambda field: item[field['name']], self.model.fields)),
            deck_id=self.deck_id
        )

    # Create list of dicts, where each dict has all fields specified in self.model + id.
    def process_file(self, file_path: str) -> None:
        with open(file_path) as file:
            lines = nonblank_lines(file)
            lines = list(filter(None, lines))  # Filter empty lines.

            fields_with_id = self.model.fields.copy()
            fields_with_id.insert(0, {'name': 'id'})

            num_vals = len(fields_with_id)

            if len(lines) % num_vals != 0:
                raise ValueError("Wrong file format")

            for i in range(0, len(lines), num_vals):
                card = {}
                j = 0
                for field in fields_with_id:
                    if DEBUG:
                        print(field)
                    card[field['name']] = lines[i + j]
                    j += 1
                if DEBUG:
                    print(card)
                self.cards.append(card)

    def export(self) -> None:
        my_deck = genanki.Deck(self.deck_id, DECK_NAME)
        my_deck.add_model(self.model)

        for item in self.cards:
            note = self.make_note(item)
            my_deck.add_note(note)

        my_package = genanki.Package(my_deck)
        my_package.write_to_file("deck.apkg")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError("Missing parameter: release/debug")

    if sys.argv[1] == 'debug':
        if len(sys.argv) < 3:
            raise ValueError("Missing parameter: file path")
        path = sys.argv[2]

        gen = NoteGenerator(BASE_MODEL, 2137)
        gen.process_file(path)
        gen.export()

    else:
        gen = NoteGenerator(BASE_MODEL, DECK_ID)
        if len(sys.argv) < 3:
            raise ValueError("Missing parameter: file path")
        path = sys.argv[2]
        os.chdir(path)
        filenames = glob.glob('./*.txt')
        for f in filenames:
            if DEBUG:
                print(f)
            gen.process_file(f)
        gen.export()
