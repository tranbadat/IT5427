import argparse
import csv
import os
import sys


DEFAULT_TEXT_COLS = ["title", "content", "description", "tags"]


def load_terms(path):
    terms = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            term = line.strip()
            if not term or term.startswith("#"):
                continue
            terms.append(term.lower())
    return terms


def get_input_files(input_path):
    if os.path.isfile(input_path):
        return [input_path]
    if os.path.isdir(input_path):
        return [
            os.path.join(input_path, name)
            for name in os.listdir(input_path)
            if name.lower().endswith(".csv")
        ]
    raise FileNotFoundError(f"Không tìm thấy đường dẫn đầu vào: {input_path}")


def contains_sensitive(text, terms):
    if not text:
        return False
    lowered = text.lower()
    for term in terms:
        if term in lowered:
            return True
    return False


def should_drop(row, cols, terms):
    for col in cols:
        if contains_sensitive(row.get(col, ""), terms):
            return True
    return False


def resolve_output_path(input_file, output_path, is_input_dir):
    if is_input_dir:
        os.makedirs(output_path, exist_ok=True)
        return os.path.join(output_path, os.path.basename(input_file))

    if os.path.isdir(output_path):
        os.makedirs(output_path, exist_ok=True)
        return os.path.join(output_path, os.path.basename(input_file))
    return output_path


def filter_file(input_file, output_file, cols, terms):
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    kept = 0
    dropped = 0
    with open(input_file, "r", encoding="utf-8", errors="replace", newline="") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError(f"Không tìm thấy header trong {input_file}")

        with open(output_file, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if should_drop(row, cols, terms):
                    dropped += 1
                    continue
                writer.writerow(row)
                kept += 1

    return kept, dropped


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Loại bỏ bài viết chứa từ nhạy cảm trong file CSV."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="File CSV đầu vào hoặc thư mục chứa các file CSV.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="File CSV đầu ra hoặc thư mục chứa các file đã lọc.",
    )
    parser.add_argument(
        "--words",
        default=os.path.join("configs", "sensitive_words.txt"),
        help="Đường dẫn danh sách từ nhạy cảm.",
    )
    parser.add_argument(
        "--text-cols",
        default=",".join(DEFAULT_TEXT_COLS),
        help="Danh sách cột văn bản cần quét, ngăn cách bởi dấu phẩy.",
    )
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    terms = load_terms(args.words)
    if not terms:
        raise ValueError("Danh sách từ nhạy cảm đang trống.")

    cols = [col.strip() for col in args.text_cols.split(",") if col.strip()]
    input_files = get_input_files(args.input)
    is_input_dir = os.path.isdir(args.input)

    total_kept = 0
    total_dropped = 0
    for input_file in input_files:
        output_file = resolve_output_path(input_file, args.output, is_input_dir)
        kept, dropped = filter_file(input_file, output_file, cols, terms)
        total_kept += kept
        total_dropped += dropped
        print(
            f"Đã lọc {os.path.basename(input_file)} -> {output_file} "
            f"(giữ lại={kept}, loại bỏ={dropped})"
        )

    print(f"Hoàn tất. giữ lại={total_kept}, loại bỏ={total_dropped}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        sys.exit(1)
