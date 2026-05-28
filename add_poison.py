# Adds junk text in an attempt to make fics unuseable to train AI
# By TricksOfLoki
# Updated 5/26/2025

from io import open
from os.path import exists, isfile
from random import randint, choice
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("filename", type=str, help="input file location")
    parser.add_argument("-m", "--mode", default="default", help="tame or default")
    parser.add_argument("-c", "--class", default="poison", type=str, help="poison class name (default: poison)")

    args = parser.parse_args()
    config = vars(args)

    return config["filename"], config["mode"], config["class"]


def is_chinese(text: str, portion_threshold: float = 0.2) -> bool:
    """
    Detect whether a text is written in Chinese.

    Checks the proportion of Chinese characters (CJK Unified Ideographs and
    common extensions) relative to all non-whitespace characters. Returns True
    if the proportion meets or exceeds `portion_threshold` (default: 0.2, i.e.
    20%). Raising the threshold makes detection stricter; lowering it makes it
    more permissive. The default of 0.2 reliably distinguishes Chinese prose
    (typically 80–100% CJK characters) from texts that merely contain
    occasional CJK punctuation or mixed-script content.
    """
    def _is_cjk(ch: str) -> bool:
        cp = ord(ch)
        return (
            0x4E00 <= cp <= 0x9FFF   # CJK Unified Ideographs (core block)
            or 0x3400 <= cp <= 0x4DBF  # CJK Extension A
            or 0x20000 <= cp <= 0x2A6DF  # CJK Extension B
            or 0xF900 <= cp <= 0xFAFF  # CJK Compatibility Ideographs
        )

    non_ws = [ch for ch in text if not ch.isspace()]
    if not non_ws:
        return False

    chinese_count = sum(1 for ch in non_ws if _is_cjk(ch))
    return (chinese_count / len(non_ws)) >= portion_threshold


def inject_junk(text: str, chinese: bool, poison_class: str = "poison") -> str:
    """
    Inject random junk into an HTML string at random intervals.

    Each junk fragment is wrapped in a span:
        ``<span class="{poison_class}">…</span>``

    Both HTML tags (``< ... >``) and HTML entities (``& ... ;``) are treated
    atomically — the countdown is paused inside both so junk is never inserted
    in the middle of either construct.

    The ``chinese`` flag controls junk generation:
    - If ``True``, junk consists of 1–3 randomly sampled CJK Unified Ideograph
      characters (U+4E00–U+9FFF).
    - If ``False``, junk consists of a single random word drawn from
      ``popular.txt``.

    Args:
        text:         The input HTML string to poison.
        chinese:      Whether the text is Chinese. Pass ``is_chinese(text)``
                      or supply a known value directly.
        poison_class: CSS class applied to every injected ``<span>``.

    Returns:
        The input string with junk ``<span>`` elements inserted at random
        positions in the visible text content.
    """
    if chinese:
        def _random_junk() -> str:
            length = randint(1, 3)
            return "".join(chr(randint(0x4E00, 0x9FFF)) for _ in range(length))
    else:
        with open("popular.txt", mode="r", encoding="utf-8") as f:
            words = f.read().split("\n")
        wordslen = len(words)
        def _random_junk() -> str:
            return words[randint(0, wordslen)]

    result = ""
    in_tag = False
    in_entity = False
    count = 1

    for ch in text:
        result += ch

        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif ch == "&" and not in_tag:
            in_entity = True
        elif ch == ";" and in_entity:
            in_entity = False

        counting = not in_tag and not in_entity
        if counting:
            count -= 1
        if count <= 0:
            result += f"<span class=\"{poison_class}\">{_random_junk()}</span>"
            count = randint(3, 30)

    return result


def add_poison(filename:str, mode:str, poison_class:str):
    # Check that input file exists
    if not exists(filename) or not isfile(filename):
        print("Invalid file name. Make sure file path is correct")
        quit()

    if mode == "tame":
        # Get word list
        with open("popular.txt", mode="r") as file:
            words = file.read()
            words = words.split("\n")
            wordslen = len(words)

        # Get fic stored in HTML format
        with open(filename, mode="r", encoding="utf-8") as file:
            content = file.read()

        # Add a paragraph of junk text between every regular paragraph
        split = content.split("</p>")
        split.pop(len(split)-1) # Remove final empty itemd
        if len(split) <= 3:
            print("Your text wasn't able to be split into very many paragraphs. You may want to try default mode instead")
        content = ""
        for item in split:
            content += f"{item}</p>\n"
            junk = ""
            for i in range(0, randint(10, 100)):
                junk += words[randint(0, wordslen)] + " "
            content += f"<p class=\"{poison_class}\">{junk}</p>"
        return content

    elif mode == "default":
        # Read the whole file, detect language, delegate to inject_junk
        with open(filename, mode="r", encoding="utf-8") as file:
            content = file.read()
        chinese = is_chinese(content)
        return inject_junk(content, chinese, poison_class)

    else:
        print("Invalid mode. Try tame or default")
        quit()


if __name__ == "__main__":
    filename, mode, poison_class = parse_args()

    content = add_poison(filename, mode, poison_class)

    # Save new file next to old one
    new_filename = filename.replace(".txt", "_poisoned.txt")
    with open(new_filename, mode="w", encoding="utf-8") as new_file:
        new_file.write(content)
    print(f"Saved to {new_filename}")