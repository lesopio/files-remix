import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class FrameworkHint:
    name: str
    reason: str


FRAMEWORK_RULES = {
    ".js": [
        FrameworkHint("React 18 + Vite", "great DX, JSX matches .js tooling"),
        FrameworkHint("Vue 3 + Vite", "single-file components pair nicely with JS"),
        FrameworkHint("SvelteKit", "small bundles when authoring plain JS"),
    ],
    ".ts": [
        FrameworkHint("React 18 + TypeScript", "strong TS ecosystem and typings"),
        FrameworkHint("Vue 3 + `<script setup lang='ts'>`", "tight TS support"),
        FrameworkHint("SolidStart", "built with TypeScript-first mindset"),
    ],
    ".jsx": [
        FrameworkHint("React 18", "native support for JSX syntax"),
        FrameworkHint("Preact", "drop-in JSX compatible and ultra light"),
    ],
    ".tsx": [
        FrameworkHint("React 18 + TypeScript", "TSX is React's native dialect"),
        FrameworkHint("SolidJS", "TSX templating and fine-grained reactivity"),
    ],
    ".vue": [
        FrameworkHint("Vue 3", "SFCs map 1:1 to .vue files"),
        FrameworkHint("Nuxt 3", "meta-framework for Vue single-file components"),
    ],
    ".svelte": [
        FrameworkHint("SvelteKit", "first-class support for .svelte files"),
    ],
    ".astro": [
        FrameworkHint("Astro", "Astro components live in .astro files"),
    ],
    ".html": [
        FrameworkHint("Astro", "island architecture over HTML heavy sites"),
        FrameworkHint("Lit", "web components layered on HTML templates"),
    ],
    ".css": [
        FrameworkHint("Vanilla Extract", "type-safe styling atop CSS"),
        FrameworkHint("Tailwind Play CDN", "utility-first styling within CSS"),
    ],
}

COLOR_PALETTE = {
    "smog_blue": "#6E7B8B",  # 雾霾蓝
    "lemon_yellow": "#FFF44F",  # 柠檬黄
    "sunset_red": "#FF4500",  # 日落红
}


def gather_files(root: Path, suffix: str) -> List[Path]:
    suffix = suffix.lower()
    return sorted([p for p in root.rglob(f"*{suffix}") if p.is_file()])


def merge_files(files: Iterable[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_chunks = []
    for file_path in files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        try:
            display_path = file_path.relative_to(Path.cwd())
        except ValueError:
            display_path = file_path
        header = f"\n\n----- {display_path} -----\n"
        merged_chunks.append(header + content)
    output_path.write_text("".join(merged_chunks).lstrip(), encoding="utf-8")


def suggest_frameworks(extension: str) -> List[FrameworkHint]:
    return FRAMEWORK_RULES.get(extension.lower(), [
        FrameworkHint("Vite + React/Vue/Svelte", "good default when unsure"),
        FrameworkHint("Astro", "handles mixed frameworks and static assets well"),
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Match a front-end framework and merge files by extension."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan (defaults to current working directory).",
    )
    parser.add_argument(
        "--extension",
        required=True,
        help="File suffix to merge, e.g. .js or .vue.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for merged output file. Defaults to root/combined.<ext>.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    extension = args.extension if args.extension.startswith(".") else f".{args.extension}"
    root = args.root.resolve()
    output = args.output or root / f"combined{extension}"

    files = gather_files(root, extension)
    if not files:
        print(f"No files ending with {extension} were found under {root}.")
        return

    merge_files(files, output.resolve())
    hints = suggest_frameworks(extension)

    print(f"Merged {len(files)} files into {output}")
    print("\nSuggested frameworks for this stack:")
    for hint in hints:
        print(f"- {hint.name}: {hint.reason}")

    print("\nFront-end palette (雾霾蓝 / 柠檬黄 / 日落红):")
    for label, hex_code in COLOR_PALETTE.items():
        print(f"- {label}: {hex_code}")


if __name__ == "__main__":
    main()

