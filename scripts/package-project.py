"""Empacota fontes, documentação e assets para a entrega acadêmica local."""

import argparse
from pathlib import Path
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ("backend", "dist", "docs", "scripts", "tests")
SOURCE_FILES = (
    "README.md", "ARTWORK.md", ".gitignore", "package.json", "package-lock.json",
    "playwright.config.mjs", "playwright.api.config.mjs", "requirements.txt", "requirements-test.txt",
)
IGNORED_DIRECTORIES = {"__pycache__", ".cache", "data", ".venv", "node_modules", ".git"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PROJECT.parent / "petal-and-stem-entrega.zip")
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    candidates = [PROJECT / name for name in SOURCE_FILES]
    for name in SOURCE_DIRECTORIES:
        candidates.extend((PROJECT / name).rglob("*"))
    files = []
    for file in candidates:
        relative = file.relative_to(PROJECT)
        if (file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(PROJECT)
                and not IGNORED_DIRECTORIES.intersection(relative.parts)
                and file.suffix not in {".pyc", ".pyo", ".sqlite3", ".zip"}):
            files.append(file)
    if output in [file.resolve() for file in files]:
        raise SystemExit("O arquivo de saída não pode substituir um arquivo-fonte.")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Não substitui uma entrega anterior silenciosamente.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(files):
            archive.write(file, Path(PROJECT.name) / file.relative_to(PROJECT))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Falha na verificação do ZIP.")
    print(f"ZIP criado e verificado: {output} ({len(files)} arquivos)")


if __name__ == "__main__":
    main()
