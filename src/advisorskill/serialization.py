"""Decode proposal and import metadata without executing embedded content."""

import yaml
from yaml.events import AliasEvent

from advisorskill.storage import AdvisorError, unique_object


class DataLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(AliasEvent):
            raise AdvisorError("YAML aliases are unsupported.")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        return unique_object(self.construct_pairs(node, deep=deep))


def read_yaml(text: str, label: str):
    try:
        return yaml.load(text, Loader=DataLoader)
    except (yaml.YAMLError, TypeError, ValueError, OverflowError, RecursionError):
        raise AdvisorError(f"{label} is invalid YAML.") from None
