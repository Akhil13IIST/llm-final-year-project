"""
UPPAAL RAG (Retrieval-Augmented Generation) System
Uses 295 UPPAAL reference models to improve LLM generation accuracy
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import xml.etree.ElementTree as ET

class UppaalRAG:
    def __init__(self, corpus_path="uppaal-models-main", cache_file="uppaal_rag_cache.pkl"):
        self.corpus_path = corpus_path
        self.cache_file = cache_file
        self.examples = []
        self.embedder = None
        self.index = None
        
        # Try to load from cache first
        if os.path.exists(cache_file):
            print("📚 Loading UPPAAL corpus from cache...")
            self.load_from_cache()
        else:
            print("🔨 Building UPPAAL corpus index (one-time, ~2-3 minutes)...")
            self.build_index()
            self.save_to_cache()
    
    def build_index(self):
        """Index all UPPAAL models from corpus"""
        try:
            # Import here to avoid dependency if using cache
            from sentence_transformers import SentenceTransformer
            import faiss
            
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast, CPU-friendly
            
            print(f"📁 Scanning {self.corpus_path} for UPPAAL models...")
            
            # Collect all .xml files
            xml_count = 0
            for root, dirs, files in os.walk(self.corpus_path):
                for file in files:
                    if file.endswith('.xml'):
                        filepath = os.path.join(root, file)
                        try:
                            example = self.extract_model_info(filepath)
                            if example:
                                self.examples.append(example)
                                xml_count += 1
                                if xml_count % 50 == 0:
                                    print(f"  Processed {xml_count} models...")
                        except Exception as e:
                            # Skip files that can't be parsed
                            pass
            
            print(f"✅ Found {len(self.examples)} valid UPPAAL models")
            
            if not self.examples:
                print("⚠️ No UPPAAL models found in corpus. RAG will use fallback mode.")
                return
            
            # Create embeddings
            print("🧮 Creating embeddings...")
            descriptions = [ex['search_text'] for ex in self.examples]
            embeddings = self.embedder.encode(descriptions, show_progress_bar=True)
            
            # Build FAISS index for fast similarity search
            print("🔍 Building search index...")
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)  # L2 distance
            self.index.add(embeddings.astype('float32'))
            
            print(f"✅ RAG index built with {len(self.examples)} models!")
            
        except ImportError as e:
            print(f"⚠️ RAG dependencies not installed: {e}")
            print("   Install with: pip install sentence-transformers faiss-cpu")
            self.examples = []
            self.embedder = None
            self.index = None
    
    def extract_model_info(self, filepath: str) -> Dict:
        """Extract useful information from UPPAAL XML file"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Extract key information
            info = {
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'templates': [],
                'declarations': '',
                'system': '',
                'queries': [],
                'full_content': ''
            }
            
            # Get declarations
            decl = root.find('declaration')
            if decl is not None and decl.text:
                info['declarations'] = decl.text.strip()[:500]  # First 500 chars
            
            # Get templates (task definitions)
            for template in root.findall('template'):
                name_elem = template.find('name')
                template_name = name_elem.text if name_elem is not None else 'Unknown'
                
                # Get template declaration
                template_decl = template.find('declaration')
                template_decl_text = template_decl.text if template_decl is not None and template_decl.text else ''
                
                # Count locations and transitions
                locations = len(template.findall('location'))
                transitions = len(template.findall('transition'))
                
                info['templates'].append({
                    'name': template_name,
                    'declaration': template_decl_text[:300],
                    'locations': locations,
                    'transitions': transitions
                })
            
            # Get system definition
            system = root.find('system')
            if system is not None and system.text:
                info['system'] = system.text.strip()[:300]
            
            # Get queries (properties)
            for query in root.findall('queries/query'):
                formula_elem = query.find('formula')
                if formula_elem is not None and formula_elem.text:
                    comment_elem = query.find('comment')
                    comment = comment_elem.text if comment_elem is not None and comment_elem.text else ''
                    info['queries'].append({
                        'formula': formula_elem.text.strip(),
                        'comment': comment.strip()
                    })
            
            # Read full file content (truncated)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                info['full_content'] = f.read()[:2000]  # First 2000 chars
            
            # Create searchable text (what we'll embed)
            search_parts = [
                f"File: {info['filename']}",
                f"Templates: {', '.join([t['name'] for t in info['templates']])}",
                f"Declarations: {info['declarations']}",
                f"System: {info['system']}",
                f"Queries: {' '.join([q['formula'] for q in info['queries'][:3]])}"
            ]
            info['search_text'] = ' '.join(search_parts)
            
            # Only keep if it has actual content
            if info['templates'] or info['declarations'] or info['queries']:
                return info
            else:
                return None
            
        except Exception as e:
            # Skip problematic files
            return None
    
    def find_similar_examples(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find most similar UPPAAL models to the query"""
        
        if not self.examples or self.embedder is None or self.index is None:
            return []
        
        try:
            # Embed query
            query_embedding = self.embedder.encode([query])
            
            # Search index
            distances, indices = self.index.search(
                query_embedding.astype('float32'),
                min(top_k, len(self.examples))
            )
            
            # Return similar examples
            similar = []
            for idx, distance in zip(indices[0], distances[0]):
                example = self.examples[idx].copy()
                example['similarity_distance'] = float(distance)
                similar.append(example)
            
            return similar
            
        except Exception as e:
            print(f"⚠️ RAG search error: {e}")
            return []
    
    def augment_prompt_with_examples(self, base_prompt: str, query: str, top_k: int = 2) -> str:
        """Add relevant UPPAAL examples to the prompt"""
        
        similar = self.find_similar_examples(query, top_k)
        
        if not similar:
            # No examples found, return original prompt
            return base_prompt
        
        # Build augmented prompt
        augmented = base_prompt + "\n\n"
        augmented += "=" * 60 + "\n"
        augmented += "REFERENCE EXAMPLES FROM VERIFIED UPPAAL MODELS:\n"
        augmented += "=" * 60 + "\n\n"
        
        for i, example in enumerate(similar, 1):
            augmented += f"--- EXAMPLE {i}: {example['filename']} ---\n\n"
            
            # Add template information
            if example['templates']:
                augmented += "Templates:\n"
                for template in example['templates'][:2]:  # Max 2 templates per example
                    augmented += f"  - {template['name']} ({template['locations']} locations, {template['transitions']} transitions)\n"
                    if template['declaration']:
                        augmented += f"    Declarations: {template['declaration'][:200]}\n"
                augmented += "\n"
            
            # Add declarations
            if example['declarations']:
                augmented += f"Global Declarations:\n{example['declarations'][:400]}\n\n"
            
            # Add system definition
            if example['system']:
                augmented += f"System Definition:\n{example['system'][:300]}\n\n"
            
            # Add sample queries
            if example['queries']:
                augmented += "Verified Properties:\n"
                for query in example['queries'][:3]:  # Max 3 queries
                    augmented += f"  - {query['formula']}"
                    if query['comment']:
                        augmented += f" // {query['comment'][:50]}"
                    augmented += "\n"
                augmented += "\n"
            
            augmented += "-" * 60 + "\n\n"
        
        augmented += "Now generate UPPAAL model following similar patterns from these examples.\n"
        augmented += "=" * 60 + "\n\n"
        
        return augmented
    
    def save_to_cache(self):
        """Save index to cache file for faster loading"""
        if not self.examples:
            return
        
        try:
            cache_data = {
                'examples': self.examples,
                'model_name': 'all-MiniLM-L6-v2'
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 Saved RAG cache to {self.cache_file}")
            
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def load_from_cache(self):
        """Load index from cache file"""
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.examples = cache_data['examples']
            
            # Rebuild embedder and index
            from sentence_transformers import SentenceTransformer
            import faiss
            
            self.embedder = SentenceTransformer(cache_data['model_name'])
            
            # Rebuild FAISS index
            descriptions = [ex['search_text'] for ex in self.examples]
            embeddings = self.embedder.encode(descriptions, show_progress_bar=False)
            
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings.astype('float32'))
            
            print(f"✅ Loaded {len(self.examples)} models from cache")
            
        except Exception as e:
            print(f"⚠️ Cache load failed: {e}")
            print("   Rebuilding index from scratch...")
            self.build_index()
    
    def get_stats(self) -> Dict:
        """Get statistics about the indexed corpus"""
        if not self.examples:
            return {
                'total_models': 0,
                'error': 'No models indexed'
            }
        
        total_templates = sum(len(ex['templates']) for ex in self.examples)
        total_queries = sum(len(ex['queries']) for ex in self.examples)
        
        # Count unique template names
        template_names = set()
        for ex in self.examples:
            for template in ex['templates']:
                template_names.add(template['name'])
        
        return {
            'total_models': len(self.examples),
            'total_templates': total_templates,
            'unique_template_names': len(template_names),
            'total_queries': total_queries,
            'avg_templates_per_model': total_templates / len(self.examples) if self.examples else 0,
            'avg_queries_per_model': total_queries / len(self.examples) if self.examples else 0
        }


# Standalone test
if __name__ == "__main__":
    print("🚀 Testing UPPAAL RAG System\n")
    
    # Initialize
    rag = UppaalRAG()
    
    # Show stats
    stats = rag.get_stats()
    print("\n📊 Corpus Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test search
    print("\n🔍 Testing similarity search...")
    test_queries = [
        "periodic task with deadline constraint",
        "railway crossing control system",
        "mutex mutual exclusion synchronization",
        "clock timing constraint deadline"
    ]
    
    for query in test_queries:
        print(f"\n Query: '{query}'")
        results = rag.find_similar_examples(query, top_k=3)
        
        if results:
            print(f"  Found {len(results)} similar models:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result['filename']} (distance: {result['similarity_distance']:.2f})")
                if result['templates']:
                    print(f"       Templates: {', '.join([t['name'] for t in result['templates'][:3]])}")
        else:
            print("  No results found")
    
    print("\n✅ RAG test complete!")
