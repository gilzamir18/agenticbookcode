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
        entities = [line.split("—")[0].strip() for line in entities_block.split("\n") if line.strip()]
        dataset.append({"text": text, "entities": entities})
    return dataset


async def evaluate_model(model, dataset):
    results = []
    for item in dataset:
        text = item["text"]
        true_entities = set(item["entities"])
        predicted_entities = set(await model.extract_entities(text))
        precision = len(predicted_entities & true_entities) / len(predicted_entities) if predicted_entities else 0
        recall = len(predicted_entities & true_entities) / len(true_entities) if true_entities else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
        results.append({
            "text": text,
            "true_entities": true_entities,
            "predicted_entities": predicted_entities,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        })

    n = len(results)
    averages = {
        "avg_precision": sum(r["precision"] for r in results) / n if n else 0,
        "avg_recall": sum(r["recall"] for r in results) / n if n else 0,
        "avg_f1_score": sum(r["f1_score"] for r in results) / n if n else 0,
    }
    return results, averages
