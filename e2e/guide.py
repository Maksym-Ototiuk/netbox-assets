"""
The YAML blocks of docs/cable-assembly-profiles.md.

The end-to-end tests import exactly these blocks, so the guide cannot drift
from what NetBox and the plugin do.
"""

import re
from pathlib import Path

import yaml

DOC = Path(__file__).resolve().parent.parent / 'docs' / 'cable-assembly-profiles.md'
TEXT = DOC.read_text()


def yaml_blocks():
    """All ```yaml blocks of the guide, in order."""
    return re.findall(r'```yaml\n(.*?)```', TEXT, re.S)


def documents(block):
    """(text, data) of each YAML document of a block (documents are separated by ---)."""
    return list(zip(block.split('---\n'), yaml.safe_load_all(block)))


def profile_blocks():
    """{profile name: [YAML text of each block that defines it]}"""
    profiles = {}
    for block in yaml_blocks():
        for text, data in documents(block):
            if 'schema' in data:
                profiles.setdefault(data['name'], []).append(text)
    return profiles


def profile(name):
    """The YAML text of a profile (the same in every block that defines it)."""
    return profile_blocks()[name][0]


def module_type_blocks():
    """[(block text, [module type data of each document])] in the order of the guide."""
    return [
        (block, [data for _text, data in documents(block)])
        for block in yaml_blocks()
        if 'schema' not in yaml.safe_load_all(block).__next__()
    ]


def module_type_block(model):
    """The block that defines a module type, with the data of its documents."""
    for block, docs in module_type_blocks():
        if any(data['model'] == model for data in docs):
            return block, docs
    raise KeyError(f'No module type {model} in {DOC.name}')


def assert_documented(*texts):
    """Fail if the guide does not mention each text (the values the tests expect)."""
    flat = ' '.join(TEXT.split())
    missing = [text for text in texts if text not in flat]
    assert not missing, f'{DOC.name} does not mention {missing}'
