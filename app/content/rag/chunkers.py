"""
Document chunking implementations for the RAG system.

This module provides concrete implementations of the IChunker interface
for splitting large documents into searchable chunks.
"""

import re
from typing import Any, Dict, List

from langchain_core.documents import Document

from .interfaces import IChunker


class MarkdownChunker(IChunker):
    """
    Chunks markdown-formatted documents by respecting their structure.

    This chunker is particularly suited for lore documents and other
    markdown-formatted content. It preserves section hierarchy and
    ensures chunks maintain context.
    """

    def chunk(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[Document]:
        """
        Split markdown content into chunks while preserving structure.

        The chunker recognizes markdown headers (##, ###) and attempts to:
        1. Keep sections together when possible
        2. Split large sections at paragraph boundaries
        3. Preserve section context in chunk metadata

        Args:
            content: Markdown-formatted text content
            metadata: Base metadata to include with each chunk
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Amount of overlap between chunks (not used in current implementation)

        Returns:
            List of Document objects with structured metadata
        """
        documents = []

        # Split content by major sections (## headers)
        sections = content.split("\n## ")

        for section_idx, section in enumerate(sections):
            # Skip empty sections
            if not section.strip():
                continue

            # For the first section, it might not have ## prefix
            if section_idx == 0 and not section.startswith("#"):
                # This is content before any ## header
                if len(section.strip()) > chunk_size:
                    # Chunk it
                    chunks = self._chunk_text(section.strip(), chunk_size)
                    for chunk_idx, chunk_text in enumerate(chunks):
                        if chunk_text:
                            doc_metadata = metadata.copy()
                            doc_metadata.update(
                                {
                                    "type": "lore_intro",
                                    "chunk_index": chunk_idx,
                                }
                            )
                            documents.append(
                                Document(page_content=chunk_text, metadata=doc_metadata)
                            )
                else:
                    # Small enough to be one document
                    if section.strip():
                        doc_metadata = metadata.copy()
                        doc_metadata["type"] = "lore_intro"
                        documents.append(
                            Document(
                                page_content=section.strip(), metadata=doc_metadata
                            )
                        )
                continue

            # Extract section name and content
            lines = section.split("\n", 1)
            section_name = lines[0].strip()
            section_content = lines[1].strip() if len(lines) > 1 else ""

            if not section_content:
                continue

            # Check if section has subsections (### headers)
            if "\n### " in section_content:
                # Process subsections
                subsections = section_content.split("\n### ")

                for subsection_idx, subsection in enumerate(subsections):
                    if subsection_idx == 0:
                        # Content before first ### header
                        if subsection.strip():
                            # Limit to reasonable size
                            truncated = subsection.strip()[:1000]
                            doc_metadata = metadata.copy()
                            doc_metadata.update(
                                {
                                    "type": "lore_section",
                                    "section": section_name,
                                }
                            )
                            documents.append(
                                Document(
                                    page_content=f"{section_name}: {truncated}",
                                    metadata=doc_metadata,
                                )
                            )
                    else:
                        # Process subsection
                        sublines = subsection.split("\n", 1)
                        if len(sublines) >= 2:
                            subsection_name = sublines[0].strip()
                            subsection_content = sublines[1].strip()

                            if subsection_content:
                                # Chunk large subsections
                                chunks = self._chunk_text(
                                    subsection_content, chunk_size
                                )
                                for chunk_idx, chunk_text in enumerate(chunks):
                                    if chunk_text:
                                        doc_metadata = metadata.copy()
                                        doc_metadata.update(
                                            {
                                                "type": "lore_subsection",
                                                "section": section_name,
                                                "subsection": subsection_name,
                                                "chunk_index": chunk_idx,
                                            }
                                        )
                                        documents.append(
                                            Document(
                                                page_content=f"{section_name} - {subsection_name}: {chunk_text}",
                                                metadata=doc_metadata,
                                            )
                                        )
            else:
                # No subsections, chunk the section if needed
                if len(section_content) > chunk_size * 2:
                    # Large section, needs chunking
                    chunks = self._chunk_text(section_content, chunk_size)
                    for chunk_idx, chunk_text in enumerate(chunks):
                        if chunk_text:
                            doc_metadata = metadata.copy()
                            doc_metadata.update(
                                {
                                    "type": "lore_section",
                                    "section": section_name,
                                    "chunk_index": chunk_idx,
                                }
                            )
                            documents.append(
                                Document(
                                    page_content=f"{section_name}: {chunk_text}",
                                    metadata=doc_metadata,
                                )
                            )
                else:
                    # Small enough for one document
                    doc_metadata = metadata.copy()
                    doc_metadata.update(
                        {
                            "type": "lore_section",
                            "section": section_name,
                        }
                    )
                    documents.append(
                        Document(
                            page_content=f"{section_name}: {section_content}",
                            metadata=doc_metadata,
                        )
                    )

        return documents

    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks at word boundaries.

        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk

        Returns:
            List of text chunks
        """
        chunks = []
        words = text.split()

        # Estimate words per chunk (rough approximation)
        words_per_chunk = chunk_size // 5  # Assume average word length of 5

        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i : i + words_per_chunk]
            chunk_text = " ".join(chunk_words)
            if chunk_text:
                chunks.append(chunk_text)

        return chunks


class SimpleTextChunker(IChunker):
    """
    Simple text chunker that splits on sentence boundaries.

    This is a general-purpose chunker for non-structured text.
    """

    def chunk(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> List[Document]:
        """
        Split text into chunks at sentence boundaries with overlap.

        Args:
            content: Text content to chunk
            metadata: Base metadata to include with each chunk
            chunk_size: Target size for each chunk
            chunk_overlap: Amount of overlap between chunks

        Returns:
            List of Document objects
        """
        documents: List[Document] = []

        # Split into sentences (simple approach)
        sentences = re.split(r"(?<=[.!?])\s+", content)

        current_chunk: List[str] = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > chunk_size and current_chunk:
                # Create document from current chunk
                chunk_text = " ".join(current_chunk)
                doc_metadata = metadata.copy()
                doc_metadata["chunk_index"] = len(documents)

                documents.append(
                    Document(page_content=chunk_text, metadata=doc_metadata)
                )

                # Start new chunk with overlap
                if chunk_overlap > 0 and len(current_chunk) > 1:
                    # Keep last few sentences for overlap
                    overlap_sentences: List[str] = []
                    overlap_size = 0

                    for sent in reversed(current_chunk):
                        if overlap_size + len(sent) <= chunk_overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_size += len(sent)
                        else:
                            break

                    current_chunk = overlap_sentences
                    current_size = overlap_size
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            doc_metadata = metadata.copy()
            doc_metadata["chunk_index"] = len(documents)

            documents.append(Document(page_content=chunk_text, metadata=doc_metadata))

        return documents
