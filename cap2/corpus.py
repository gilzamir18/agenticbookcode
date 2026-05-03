from pathlib import Path


def load_blocks(path):
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    blocks = [block.strip() for block in raw.split("\n\n")]
    return [block for block in blocks if block]


def load_dataset(corpus_path=None, entities_path=None):
    base_dir = Path(__file__).resolve().parent
    corpus_path = Path(corpus_path) if corpus_path else base_dir / "corpus.txt"
    entities_path = Path(entities_path) if entities_path else base_dir / "entities.txt"

    text_blocks = load_blocks(corpus_path)
    entity_blocks = load_blocks(entities_path)

    if len(text_blocks) != len(entity_blocks):
        raise ValueError(
            f"Corpus and entities files must have the same number of blocks: "
            f"{len(text_blocks)} != {len(entity_blocks)}"
        )

    dataset = []
    for text, entities_block in zip(text_blocks, entity_blocks):
        entities = [line.strip() for line in entities_block.split("\n") if line.strip()]
        dataset.append({"text": text, "entities": entities})
    return dataset


if __name__ == "__main__":
    dataset = load_dataset()
    for item in dataset:
        print(item)
