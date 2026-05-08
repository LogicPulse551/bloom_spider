import json
from pathlib import Path


class JsonLinesPipeline:
    def open_spider(self, spider):
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        self.file = (output_dir / "qq_hot_rank_books.jl").open(
            "a", encoding="utf-8"
        )

    def close_spider(self, spider):
        if getattr(self, "file", None):
            self.file.close()

    def process_item(self, item, spider):
        self.file.write(
            json.dumps(dict(item), ensure_ascii=False, sort_keys=True) + "\n"
        )
        self.file.flush()
        return item
