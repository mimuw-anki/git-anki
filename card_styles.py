import genanki
MODEL_ID = 148814881488
CSS = """.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
}
"""
FRONT = """{{question}}"""
BACK = """{{FrontSide}}<hr id="answer">{{answer}}"""

BASE_MODEL = genanki.Model(
    MODEL_ID,
    "Base model for mimuw-anki",
    fields=[
        {"name": "id"},
        {"name": "question"},
        {"name": "answer"},
    ],
    templates=[
        {
            "name": "Card",
            "qfmt": FRONT,
            "afmt": BACK,
        },
    ],
    css=CSS,
)
