"""Bound owner-run CLI file access to working, staging and document locations.

These tools are not services. Nevertheless an accidental CLI value must not
reach system files or credential directories. Resolve links before checking a
separator-terminated root; retain the lexical path so callers can still reject
symlinks themselves. No caller-supplied root can widen this boundary.
"""
import os
from pathlib import Path
import tempfile

PROJECT = Path(__file__).resolve().parent.parent
DOCUMENT_DIRS = ('Desktop', 'Downloads', 'Documents', 'Pictures')


def allowed_roots():
    roots = [PROJECT, Path(tempfile.gettempdir()), Path('/tmp'), Path('/Volumes')]
    roots.extend(Path.home() / name for name in DOCUMENT_DIRS)
    # GitHub's isolated runner stages artifacts outside checkout and /tmp.
    if os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_TEMP'):
        roots.append(Path(os.environ['RUNNER_TEMP']))
    return tuple(dict.fromkeys(path for root in roots
                               for path in (os.path.abspath(root), os.path.realpath(root))))


def local_path(value):
    """Accept only approved storage roots and their descendants."""
    raw = os.fspath(value)
    if not raw or '\x00' in raw or any(ord(char) < 32 for char in raw):
        raise ValueError('Empty/control-character local path rejected')
    lexical = os.path.abspath(os.path.expanduser(raw))
    canonical = os.path.realpath(lexical)
    if not any(canonical == root or canonical.startswith(root + os.sep)
               for root in allowed_roots()):
        raise ValueError('Local path symlink escapes the approved storage locations')
    for root in allowed_roots():
        if lexical == root:
            return Path(root)
        if lexical.startswith(root + os.sep):
            return Path(lexical)
    raise ValueError('Local path must be inside the project, a document folder, temporary staging or /Volumes')


def child_path(root, name):
    """Select a regular-tree descendant; never follow a link from an archive/site."""
    root = Path(root).resolve()
    relative = Path(name)
    if (relative.is_absolute() or not relative.parts or '..' in relative.parts
            or '\\' in str(name) or any(ord(char) < 32 for char in str(name))):
        raise ValueError('Invalid relative file path')
    candidate = root / relative
    for entry in (candidate, *candidate.parents):
        if entry == root:
            break
        if entry.is_symlink():
            raise ValueError('Symlinked file path rejected')
    canonical = os.path.realpath(candidate)
    if canonical.startswith(str(root) + os.sep):
        return Path(canonical)
    raise ValueError('File path escapes its selected root')
