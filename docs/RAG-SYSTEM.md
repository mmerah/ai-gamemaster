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

The system includes five core knowledge bases located in the `knowledge/` directory:

### Rules (`rules.json`)
- Attack rolls and damage mechanics
- Spellcasting rules and saving throws
- Combat actions and initiative
- Conditions and status effects
- Resting and recovery rules

### Spells (`spells.json`)
- Spell descriptions and mechanics
- Casting requirements and components
- Spell slot usage and limitations
- School-specific spell effects

### Monsters (`monsters.json`)
- Creature statistics and abilities
- Combat tactics and behaviors
- Special attacks and defenses
- Challenge ratings and encounter balance

### Lore (`lore.json`)
- World-building and setting information
- NPC backgrounds and motivations
- Location descriptions and history
- Adventure hooks and plot elements

### Equipment (`equipment.json`)
- Weapon statistics and properties
- Armor types and AC values
- Adventuring gear and tools
- Magic item properties and effects

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

- **Performance Impact**: Loading embeddings takes 10+ seconds on startup
- **Basic Implementation**: Uses HuggingFace embeddings for semantic search
- **Manual Knowledge Base**: The knowledge bases are manually curated and may be incomplete
- **Static Filtering**: Relevance scoring is rule-based rather than learned
- **Memory Usage**: Embedding model increases memory footprint

## Technical Details

The RAG system consists of several components:

- **`app/core/rag_interfaces.py`**: Core interfaces and data models
- **`app/services/rag/rag_service.py`**: Main RAG service implementation
- **`app/services/rag/query_engine.py`**: Action analysis and query generation
- **`app/services/rag/knowledge_bases.py`**: Knowledge base implementations
- **`app/routes/rag_routes.py`**: API endpoints for RAG operations

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
