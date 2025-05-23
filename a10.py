import re, string, calendar
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from nltk import word_tokenize, pos_tag, ne_chunk
from nltk.tree import Tree
from match import match
from typing import List, Callable, Tuple, Any, Match

print("LOADING BOT MODULE!")
def get_page_html(title: str) -> str:
    """Gets html of a wikipedia page

    Args:
        title - title of the page

    Returns:
        html of the page
    """
    results = wikipedia.search(title)
    return WikipediaPage(results[0]).html()


def get_first_infobox_text(html: str) -> str:
    """Gets first infobox html from a Wikipedia page (summary box)

    Args:
        html - the full html of the page

    Returns:
        html of just the first infobox
    """
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text


def clean_text(text: str) -> str:
    """Cleans given text removing non-ASCII characters and duplicate spaces & newlines

    Args:
        text - text to clean

    Returns:
        cleaned text
    """
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    """Finds regex matches for a pattern

    Args:
        text - text to search within
        pattern - pattern to attempt to find within text
        error_text - text to display if pattern fails to match

    Returns:
        text that matches
    """
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match


def get_polar_radius(planet_name: str) -> str:
    """Gets the radius of the given planet

    Args:
        planet_name - name of the planet to get radius of

    Returns:
        radius of the given planet
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius.*?)(?: ?[\d]+ )?(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)

    return match.group("radius")


def get_birth_date(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of the person

    Returns:
        birth date of the given person
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = (
        "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("birth")


# below are a set of actions. Each takes a list argument and returns a list of answers
# according to the action and the argument. It is important that each function returns a
# list of the answer(s) and not just the answer itself.


def birth_date(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of person's name to find birth date of

    Returns:
        birth date of named person
    """
    return [get_birth_date(" ".join(matches))]


def polar_radius(matches: List[str]) -> List[str]:
    """Returns polar radius of planet in matches

    Args:
        matches - match from pattern of planet to find polar radius of

    Returns:
        polar radius of planet
    """
    return [get_polar_radius(matches[0])]

def get_death_date(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Died\D*?)(?P<death>[A-Za-z]+\s+\d{1,2},\s+\d{4})"

    error_text = "Page infobox has no death information (in 'Month DD, YYYY' format)"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("death")



def death_date(matches: List[str]) -> List[str]:
    """Reaturns date of death of the named person in matches

    Args:
        matches - match from pattern of person's name to find date of death
    
    Returns: 
        date of death of named person
    """
    return [get_death_date(" ".join(matches))]

def get_gravity(planet_name: str) -> str:
    """Gets the gravity of the given planet

    Args: 
        planet_name - name of the planet to get gravity of

    Returns:
        gravity of the given planet
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Gravity.*?)(?P<gravity>[\d,.]+)(?:.*?)m/s"
    error_text = "Page infobox has no gravity information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("gravity") + " m/s²"




def gravity(matches: List[str]) -> List[str]:
    """Returns gravity of planet in matches

    Args: 
        matches - match from pattern of planet to find gravity of

    Returns:
        gravity of planet
    """
    return [get_gravity(matches[0])]

import datetime

def get_age(name: str) -> str:
    """Compute age of a person given their Wikipedia infobox birth (and death) dates."""
    # parse birth date (expects YYYY-MM-DD)
    birth_str = get_birth_date(name)
    birth = datetime.datetime.strptime(birth_str, "%Y-%m-%d").date()

    # try to get death date; if missing, use today
    try:
        death_str = get_death_date(name)
        end = datetime.datetime.strptime(death_str, "%Y-%m-%d").date()
    except AttributeError:
        end = datetime.date.today()  # uses system date

    # compute full years difference
    years = end.year - birth.year
    # subtract one if we haven’t reached birthday this year
    if (end.month, end.day) < (birth.month, birth.day):
        years -= 1

    return str(years)

def age(matches: List[str]) -> List[str]:
    """Returns age of the named person in matches."""
    return [get_age(" ".join(matches))]



# dummy argument is ignored and doesn't matter
def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt


# type aliases to make pa_list type more readable, could also have written:
# pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [...]
Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

# The pattern-action list for the natural language query system. It must be declared
# here, after all of the function definitions
pa_list: List[Tuple[Pattern, Action]] = [
    ("when was % born".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("when did % die".split(), death_date),
    ("what is the gravity of %".split(), gravity),
    ("how old is %".split(), age),    
    (["bye"], bye_action),
]


def search_pa_list(src: List[str]) -> List[str]:
    # debug: show exactly what patterns we're testing
    print("PATTERNS:", [pat for pat, _ in pa_list])
    for pat, act in pa_list:
        print(f"Trying {pat} against {src}")
        mat = match(pat, src)
        if mat is not None:
            print(f"  matched → {mat}")
            return act(mat) or ["No answers"]
    return ["I don't understand"]

def normalize(question: str) -> List[str]:
    cleaned = re.sub(r"[^\w\s]", "", question)
    return cleaned.lower().split()


def query_loop() -> None:
    print("Welcome to the Wikipedia bot!\n")
    while True:
        try:
            raw = input("Your query? ")
            tokens = normalize(raw)
            answers = search_pa_list(tokens)
            for ans in answers:
                print(ans)
        except (KeyboardInterrupt, EOFError):
            break
    print("\nSo long!\n")

# uncomment the next line once you've implemented everything are ready to try it out
query_loop()
