# RAG System

> **Note: The RAG system is optional and disabled by default for faster startup. Set `RAG_ENABLED=true` in your `.env` file to enable it.**

The RAG (Retrieval-Augmented Generation) system enhances the AI Game Master with context-aware D&D 5e knowledge. When enabled, it automatically retrieves relevant rules, spells, monster information, and lore to provide the AI with accurate game context.

## What It Does

The RAG system analyzes player actions and automatically injects relevant D&D 5e information into the AI's context:

- **Smart Query Generation**: Converts player actions into targeted knowledge queries
- **Multi-Source Retrieval**: Searches across rules, spells, monsters, and lore databases
- **Relevance Filtering**: Only includes the most pertinent information to avoid prompt bloat
- **Context Enhancement**: Provides the AI with accurate D&D 5e knowledge for better responses

## Knowledge Bases

The RAG system retrieves content from multiple sources:

### Database Content (Primary)
The system performs semantic search across the SQLite database tables:
- **Spells**: Spell descriptions, mechanics, and effects
- **Monsters**: Creature statistics, abilities, and behaviors
- **Equipment**: Weapons, armor, and magic items
- **Classes & Features**: Character classes and their abilities
- **Rules**: Game mechanics and conditions

### Knowledge Files (Secondary)
Additional knowledge bases in `app/content/data/knowledge/`:
- **Rules**: Combat mechanics, conditions, and game rules
- **Lore**: World-building and setting information

## How It Works

1. **Action Analysis**: When a player submits an action, the RAG query engine analyzes the text
2. **Query Generation**: Creates targeted queries based on detected keywords and context
3. **Knowledge Retrieval**: Searches relevant knowledge bases for matching information
4. **Smart Filtering**: Applies relevance scoring and deduplication to optimize results
5. **Context Injection**: Adds the most relevant knowledge to the AI's prompt

## Example Workflow

```
Player Action: "I cast Fireball at the goblins"
│
├─ RAG Analysis: Detects spell casting + specific spell + combat
├─ Generated Queries:
│  ├─ "Fireball spell mechanics and damage"
│  ├─ "Spellcasting rules and saving throws"
│  └─ "Combat actions and area effects"
│
├─ Knowledge Retrieved:
│  ├─ Fireball: "3rd-level evocation, 20-foot radius, Dex save..."
│  ├─ Spell Save DC: "8 + spellcasting modifier + proficiency..."
│  └─ Area Effects: "Creatures in area make saving throws..."
│
└─ AI Response: Uses retrieved knowledge for accurate spell resolution
```

## Configuration

Enable the RAG system by setting `RAG_ENABLED=true` in your `.env` file:

```bash
# Enable RAG for enhanced D&D 5e knowledge
RAG_ENABLED=true

# Or disable for faster startup (default)
RAG_ENABLED=false
```

When enabled, it operates with these default settings:

- **Relevance Threshold**: 2.0 (minimum score for inclusion)
- **Max Results Per Category**: 2 items
- **Max Total Results**: 5 items
- **Similarity Threshold**: 0.7 (for deduplication)

## Current Limitations

- **Performance Impact**: Initial embedding generation can take time
- **SQLite-vec**: Uses native vector search extension when available
- **Hybrid Search**: Combines database content with knowledge files
- **Embedding Model**: Uses sentence-transformers/all-MiniLM-L6-v2
- **Memory Usage**: Embedding model increases memory footprint

## Technical Details

The RAG system is integrated into the content module:

- **`app/content/rag/`**: RAG implementation within the content module
  - `rag_service.py`: Main RAG service implementation
  - `knowledge_base.py`: In-memory vector store manager
  - `db_knowledge_base_manager.py`: Database-backed knowledge base
  - `d5e_knowledge_base_manager.py`: D&D 5e-specific knowledge manager
  - `query_engine.py`: Query analysis and generation
- **`app/content/service.py`**: ContentService integrates RAG functionality
- **Database Integration**: Uses SQLite-vec for vector similarity search
- **Embeddings**: Stored directly in database tables for efficient retrieval

## Testing

Basic unit tests are available in `tests/unit/test_rag_system.py`. Integration testing can be performed using `tests/script_test_rag_integration.py`.

## Future Improvements

Potential enhancements for the RAG system include:

- Vector embeddings for semantic similarity search
- Machine learning-based relevance scoring
- Expanded knowledge bases with more comprehensive D&D 5e content
- Real-time knowledge base updates
- Performance optimization for larger datasets
- Integration with official D&D 5e APIs

---

*This documentation reflects the current experimental state of the RAG system. As the system evolves and receives more testing, this documentation will be updated accordingly.*
