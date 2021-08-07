from common import dump_yaml

from inginious_coding_style.grades import DEFAULT_CATEGORIES


if __name__ == "__main__":
    categories = [
        {"id": d.id, "name": d.name, "description": d.description}
        for d in DEFAULT_CATEGORIES.values()
    ]
    dump_yaml("categories.yml", categories)
