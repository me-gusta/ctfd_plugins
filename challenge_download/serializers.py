from flask_sqlalchemy import Model
from sqlalchemy.orm.collections import InstrumentedList

from CTFd.models import Challenges
from CTFd.schemas.challenges import ChallengeSchema


def serialize(obj: Model) -> dict:
    """ Serializes a Model object. Returns a dict with all primitive fields.
        Recursive function. If field is a Many relationship (InstrumentedList), serializes all children."""
    attribute_names = [x for x in obj.__dir__() if not x.startswith('_')]
    out = {}
    for attr_name in attribute_names:
        attr = obj.__getattribute__(attr_name)

        if attr_name.endswith('id'):
            continue
        elif type(attr) in (int, str, bool, dict):
            out[attr_name] = attr
        elif type(attr) is InstrumentedList:
            # print(attr_name, attr)
            out[attr_name] = [serialize(x) for x in attr]
        # else:
        #     print(f'404 {type(attr)}, {attr_name}, {attr}')
    return out


def challenge_from_config(config: dict) -> Challenges:
    pass
    # challenge_class = get_chal_class(config['type'])
    # challenge = challenge_class()
    # for key, value in config.items():
    #     # if type(value) is dict:
    #     #     continue
    #     challenge.__setattr__(key, value)
    # return response
    # for i in challenge.__dir__():
    #     print(i)


if __name__ == '__main__':
    a = {"max_attempts": 0, "name": "Break da law", "requirements": {"prerequisites": [2]}, "type": "standard",
         "value": 100, "state": "visible", "description": "", "category": "kringe", "files": [],
         "tags": [{"value": "grechka"}, {"value": "pussy"}], "hints": [
            {"content": "AAAAA", "type": "standard", "cost": 10, "name": "Hint 1", "category": "hints",
             "description": "Hint for Break da law"},
            {"content": "BBBBBBBB", "type": "standard", "cost": 50, "name": "Hint 2", "category": "hints",
             "description": "Hint for Break da law"}],
         "flags": [{"data": "", "type": "static", "content": "1"}, {"data": "", "type": "regex", "content": "\\w\\d"}],
         "comments": [{"type": "challenge", "content": "ACASVASVASVASVA"},
                      {"type": "challenge", "content": "VVVVVVVVVVA"}]}

    print(challenge_from_config(a))
