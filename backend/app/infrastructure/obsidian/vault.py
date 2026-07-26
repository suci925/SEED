"""
Obsidian Vault Management.

Wraps the obsidian_parser library to provide
a clean interface for Seed to interact with
an Obsidian vault as its external knowledge base.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from obsidian_parser import Vault as ObsidianVaultParser
from obsidian_parser import Note

from app.infrastructure.obsidian.graph import (
    KnowledgeGraph,
)


class ObsidianNote:
    """
    A parsed Obsidian note with metadata.

    Wraps the raw Note object from obsidian_parser
    to expose fields needed by Seed.
    """

    def __init__(self, note: Note) -> None:
        self._note = note

    @property
    def name(self) -> str:
        """Note filename without extension."""
        return self._note.name

    @property
    def path(self) -> str:
        """Relative path within the vault."""
        return self._note.path

    @property
    def content(self) -> str:
        """Raw markdown content."""
        return self._note.content

    @property
    def tags(self) -> list[str]:
        """List of tag name strings."""
        return [t.name for t in self._note.tags]

    @property
    def links(self) -> list[str]:
        """Wiki links [[...]] found in the note."""
        return self._note.links

    @property
    def frontmatter(self) -> dict[str, Any]:
        """YAML frontmatter as a dictionary."""
        return self._note.frontmatter or {}

    def __repr__(self) -> str:
        return f"ObsidianNote(name='{self.name}', tags={self.tags})"


class ObsidianVault:
    """
    Represents an Obsidian vault on disk.

    Provides operations to list, search, and
    retrieve notes for use as Seed's knowledge base.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).resolve()

        if not self._path.is_dir():
            raise NotADirectoryError(
                f"Obsidian vault not found: {self._path}"
            )

        self._vault = ObsidianVaultParser(str(self._path))
        self._graph: KnowledgeGraph | None = None

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def path(self) -> Path:
        """Absolute path to the vault root."""
        return self._path

    @property
    def notes(self) -> list[ObsidianNote]:
        """All notes in the vault."""
        return [
            ObsidianNote(n) for n in self._vault.notes
        ]

    @property
    def note_count(self) -> int:
        """Total number of notes."""
        return len(self._vault.notes)

    # --------------------------------------------------
    # Operations
    # --------------------------------------------------

    def get_note(self, name: str) -> ObsidianNote | None:
        """
        Retrieve a single note by its filename (without .md).

        Returns None if not found.
        """

        note = self._vault.get_note(name)

        if note is None:
            return None

        return ObsidianNote(note)

    def search_by_keyword(
        self,
        query: str,
        *,
        max_results: int = 10,
    ) -> list[ObsidianNote]:
        """
        Search notes by keyword / full-text.

        Scans both note title and content
        for the query string (case-insensitive).
        """

        results: list[ObsidianNote] = []

        query_lower = query.lower()

        for note in self._vault.notes:
            if query_lower in note.name.lower():
                results.append(ObsidianNote(note))

                if len(results) >= max_results:
                    break

                continue

            if query_lower in note.content.lower():
                results.append(ObsidianNote(note))

                if len(results) >= max_results:
                    break

        return results

    def search_by_tag(
        self,
        tag: str,
        *,
        max_results: int = 50,
    ) -> list[ObsidianNote]:
        """
        Retrieve all notes that have a specific tag.
        """

        results = self._vault.get_notes_with_tag(tag)

        return [
            ObsidianNote(n) for n in results[:max_results]
        ]

    def list_all_tags(self) -> list[str]:
        """
        Return the union of all tags across the vault.
        """

        all_tags: set[str] = set()

        for note in self._vault.notes:
            for tag in note.tags:
                all_tags.add(tag.name)

        return sorted(all_tags)

    def get_backlinks(
        self,
        note_name: str,
    ) -> list[ObsidianNote]:
        """
        Get all notes that link to a given note.
        """

        results = self._vault.get_backlinks(note_name)

        return [ObsidianNote(n) for n in results]

    def render_content(
        self,
        note_name: str,
    ) -> str | None:
        """
        Render a note's content, resolving wiki links
        and embedded content into readable text.
        """

        rendered = self._vault.render_content(note_name)

        return rendered

    # --------------------------------------------------
    # Knowledge Graph
    # --------------------------------------------------

    @property
    def graph(self) -> KnowledgeGraph:
        """
        Lazy-loaded knowledge graph for the vault.
        """

        if self._graph is None:
            self._graph = KnowledgeGraph(
                vault_path=self._path,
            )
            self._graph.load()

        return self._graph

    def get_graph(self) -> KnowledgeGraph:
        """Explicit getter for the knowledge graph."""
        return self.graph

    def save_graph(self) -> None:
        """Persist the knowledge graph."""
        if self._graph is not None:
            self._graph.save()
