#!/usr/bin/env python3
"""
Pack the sasparser library into a single self-extracting Python script.

This creates a script that can be pasted into a notebook or run standalone
to extract the entire library to a folder.

Usage:
    python tools/pack_library.py > sasparser_packed.py
    python tools/pack_library.py -o sasparser_packed.py
"""

import base64
import os
import sys
import zlib
from pathlib import Path


def get_files_to_pack(src_dir: Path) -> dict[str, bytes]:
    """Get all Python files from the source directory."""
    files = {}

    for root, dirs, filenames in os.walk(src_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(src_dir.parent)
                with open(filepath, "rb") as f:
                    files[str(rel_path)] = f.read()

    return files


def create_packed_script(files: dict[str, bytes]) -> str:
    """Create the self-extracting script."""

    # Compress and encode files
    file_data = {}
    for path, content in files.items():
        compressed = zlib.compress(content, level=9)
        encoded = base64.b64encode(compressed).decode("ascii")
        file_data[path] = encoded

    # Build the script
    script = '''#!/usr/bin/env python3
"""
SASParser - Self-extracting package

This script extracts the sasparser library to the current directory.
Run it or import and call extract_sasparser() to unpack.

Usage:
    python sasparser_packed.py                    # Extract to ./sasparser
    python sasparser_packed.py /path/to/dest     # Extract to custom path

In a notebook:
    exec(open("sasparser_packed.py").read())
    extract_sasparser()

    # Or after extraction:
    import sys
    sys.path.insert(0, ".")
    from sasparser import parse, extract_tables, extract_fields
"""

import base64
import os
import sys
import zlib
from pathlib import Path

# Packed file data (compressed + base64 encoded)
_PACKED_FILES = {
'''

    # Add file data
    for path, encoded in sorted(file_data.items()):
        # Split long lines for readability
        chunks = [encoded[i:i+76] for i in range(0, len(encoded), 76)]
        if len(chunks) == 1:
            script += f'    "{path}": "{encoded}",\n'
        else:
            script += f'    "{path}": (\n'
            for chunk in chunks:
                script += f'        "{chunk}"\n'
            script += '    ),\n'

    script += '''}


def extract_sasparser(dest_dir: str | Path = ".") -> Path:
    """
    Extract the sasparser library to the destination directory.

    Args:
        dest_dir: Directory to extract to (default: current directory)

    Returns:
        Path to the extracted sasparser package
    """
    dest = Path(dest_dir)

    for rel_path, encoded_data in _PACKED_FILES.items():
        # Handle multi-line encoded strings
        if isinstance(encoded_data, tuple):
            encoded_data = "".join(encoded_data)

        # Decode and decompress
        compressed = base64.b64decode(encoded_data)
        content = zlib.decompress(compressed)

        # Create file
        file_path = dest / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        print(f"  Created: {file_path}")

    sasparser_path = dest / "sasparser"
    print(f"\\nExtracted sasparser to: {sasparser_path.absolute()}")
    print(f"\\nTo use in your code:")
    print(f"  import sys")
    print(f"  sys.path.insert(0, '{dest.absolute()}')")
    print(f"  from sasparser import parse, extract_tables, extract_fields")

    return sasparser_path


def _add_to_path(dest_dir: str | Path = ".") -> None:
    """Add the extracted package to sys.path."""
    dest = Path(dest_dir).absolute()
    if str(dest) not in sys.path:
        sys.path.insert(0, str(dest))


# Quick usage functions for notebooks
def setup_sasparser(dest_dir: str | Path = ".") -> None:
    """Extract and add to path in one call."""
    extract_sasparser(dest_dir)
    _add_to_path(dest_dir)
    print("\\nsasparser is ready to use!")


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Extracting sasparser library...")
    extract_sasparser(dest)
'''

    return script


def main():
    # Find the src directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    src_dir = project_root / "src" / "sasparser"

    if not src_dir.exists():
        print(f"Error: Source directory not found: {src_dir}", file=sys.stderr)
        sys.exit(1)

    # Get files
    files = get_files_to_pack(src_dir)
    print(f"Packing {len(files)} files...", file=sys.stderr)

    # Create packed script
    script = create_packed_script(files)

    # Output
    if len(sys.argv) > 1 and sys.argv[1] in ("-o", "--output") and len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        output_path.write_text(script)
        print(f"Written to: {output_path}", file=sys.stderr)
    else:
        print(script)


if __name__ == "__main__":
    main()
