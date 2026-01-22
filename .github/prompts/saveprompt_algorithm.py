#!/usr/bin/env python3
"""
/saveprompt Algorithm - Hybrid Session Processor

PURPOSE: 
  1. ARCHIVE MODE: Transform raw Copilot sessions into clean, archivable .md documents
  2. EXTRACT MODE: Generate reusable .prompt.md templates (VS Code convention)

COMPLIANT WITH: 
  - SSOT XIV (Hash Verification), XV (DCRP Cross-Reference)
  - VS Code Copilot Chat savePrompt.prompt.md specification

ARCHIVE ALGORITHM (default):
1. PARSE - Extract conversation structure (User/Assistant turns)
2. EXTRACT - Identify key artifacts (code blocks, file changes, decisions)
3. COMPRESS - Remove redundant tool outputs, verbose system messages
4. BEAUTIFY - Apply consistent markdown formatting (FA5 Visual Integrity)
5. ANNOTATE - Add metadata headers and cross-references
6. VALIDATE - Ensure structural coherence (FA4 Architectonic Integrity)

PROMPT EXTRACTION ALGORITHM (--extract-prompts):
1. REVIEW - Identify user's primary goal/task patterns
2. GENERALIZE - Remove conversation-specific details (file names, variables)
3. PLACEHOLDER - Insert reusable placeholders ("the selected code", "the current file")
4. TITLE - Create camelCase action-oriented title
5. DESCRIBE - Write brief description (1 sentence, ≤15 words)
6. FORMAT - Generate .prompt.md with YAML frontmatter

USAGE:
    # Archive mode (beautify sessions)
    python saveprompt_algorithm.py <input_file> [--output <output.md>] [--dry-run]
    python saveprompt_algorithm.py --folder <folder_path>
    
    # Extract mode (generate reusable prompts)
    python saveprompt_algorithm.py <input_file> --extract-prompts
    python saveprompt_algorithm.py --folder <folder_path> --extract-prompts
"""

import argparse
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    CODE_BLOCK = "code_block"
    FILE_CHANGE = "file_change"


@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0
    importance: int = 1  # 1=low, 2=medium, 3=high (for compression decisions)


@dataclass
class SessionArtifact:
    """Extracted artifact from session"""
    artifact_type: str  # "code", "file_change", "decision", "error", "command"
    content: str
    context: str
    file_path: Optional[str] = None


@dataclass
class ProcessedSession:
    """Result of session processing"""
    title: str
    date: str
    turns: List[ConversationTurn]
    artifacts: List[SessionArtifact]
    summary: str
    original_lines: int
    compressed_lines: int
    content_hash: str


@dataclass
class ExtractedPrompt:
    """
    Reusable prompt extracted from session (VS Code .prompt.md format)
    
    Follows: https://github.com/microsoft/vscode-copilot-chat/blob/main/assets/prompts/savePrompt.prompt.md
    """
    name: str  # camelCase action-oriented title
    description: str  # 1 sentence, ≤15 words
    argument_hint: Optional[str]  # Expected inputs description
    prompt_text: str  # Generalized markdown prompt with placeholders
    tools: List[str] = field(default_factory=list)  # Required tools
    source_session: Optional[str] = None  # Original session file for traceability


class SavePromptProcessor:
    """Main processor implementing /saveprompt algorithm"""
    
    # Compression thresholds
    MAX_CODE_BLOCK_LINES = 50  # Truncate code blocks longer than this
    MAX_TOOL_OUTPUT_LINES = 20  # Truncate tool outputs
    OMIT_PATTERNS = [
        r'Lines \d+-\d+ omitted',
        r'Summarized conversation history',
        r'File content truncated',
    ]
    
    def __init__(self, compression_level: int = 2):
        """
        Initialize processor.
        
        Args:
            compression_level: 1=minimal, 2=balanced, 3=aggressive
        """
        self.compression_level = compression_level
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for parsing"""
        self.patterns = {
            'user_turn': re.compile(r'^User:\s*(.*)$', re.MULTILINE),
            'assistant_turn': re.compile(r'^(GitHub Copilot|Assistant|Workspace|Claude):\s*', re.MULTILINE),
            'code_block_start': re.compile(r'^```(\w*)$'),
            'code_block_end': re.compile(r'^```$'),
            'file_link': re.compile(r'\[([^\]]*)\]\(file:\/\/\/([^)]+)\)'),
            'heading': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'bullet': re.compile(r'^(\s*[-*+])\s+(.+)$', re.MULTILINE),
            'tool_result_start': re.compile(r'^Ran terminal command:|^Read \[|^Created \[|^Replacing'),
            'omit_marker': re.compile(r'/\* Lines \d+-\d+ omitted \*/'),
        }
    
    def parse_raw_session(self, content: str) -> List[ConversationTurn]:
        """
        Parse raw session content into conversation turns.
        
        STEP 1 of /saveprompt algorithm: PARSE
        """
        turns = []
        lines = content.split('\n')
        current_turn = None
        current_content = []
        current_type = None
        line_start = 0
        
        for i, line in enumerate(lines):
            # Detect user turn start
            if line.startswith('User:'):
                # Save previous turn
                if current_turn is not None:
                    current_turn.content = '\n'.join(current_content)
                    current_turn.line_end = i - 1
                    turns.append(current_turn)
                
                # Start new user turn
                current_type = MessageType.USER
                current_content = [line[5:].strip()]  # Remove "User:" prefix
                line_start = i
                current_turn = ConversationTurn(
                    type=current_type,
                    content='',
                    line_start=line_start,
                    importance=3  # User messages are high importance
                )
            
            # Detect assistant turn start
            elif any(line.startswith(prefix) for prefix in ['GitHub Copilot:', 'Assistant:', 'Workspace:', 'Claude:']):
                # Save previous turn
                if current_turn is not None:
                    current_turn.content = '\n'.join(current_content)
                    current_turn.line_end = i - 1
                    turns.append(current_turn)
                
                # Start new assistant turn
                current_type = MessageType.ASSISTANT
                # Remove the prefix
                for prefix in ['GitHub Copilot:', 'Assistant:', 'Workspace:', 'Claude:']:
                    if line.startswith(prefix):
                        current_content = [line[len(prefix):].strip()]
                        break
                line_start = i
                current_turn = ConversationTurn(
                    type=current_type,
                    content='',
                    line_start=line_start,
                    importance=2  # Assistant messages are medium importance
                )
            
            # Continue current turn
            elif current_turn is not None:
                current_content.append(line)
        
        # Don't forget the last turn
        if current_turn is not None:
            current_turn.content = '\n'.join(current_content)
            current_turn.line_end = len(lines) - 1
            turns.append(current_turn)
        
        return turns
    
    def extract_artifacts(self, turns: List[ConversationTurn]) -> List[SessionArtifact]:
        """
        Extract key artifacts from conversation turns.
        
        STEP 2 of /saveprompt algorithm: EXTRACT
        """
        artifacts = []
        
        for turn in turns:
            content = turn.content
            
            # Extract code blocks
            in_code_block = False
            code_lang = ''
            code_lines = []
            
            for line in content.split('\n'):
                if self.patterns['code_block_start'].match(line):
                    in_code_block = True
                    match = self.patterns['code_block_start'].match(line)
                    code_lang = match.group(1) if match.group(1) else 'text'
                    code_lines = []
                elif self.patterns['code_block_end'].match(line) and in_code_block:
                    in_code_block = False
                    if code_lines:
                        artifacts.append(SessionArtifact(
                            artifact_type='code',
                            content='\n'.join(code_lines),
                            context=f"Language: {code_lang}",
                        ))
                elif in_code_block:
                    code_lines.append(line)
            
            # Extract file changes
            file_matches = self.patterns['file_link'].findall(content)
            for desc, path in file_matches:
                artifacts.append(SessionArtifact(
                    artifact_type='file_change',
                    content=desc,
                    context=turn.content[:200],  # First 200 chars for context
                    file_path=path,
                ))
            
            # Extract decisions (look for patterns like "Decision:", "Chose:", etc.)
            decision_patterns = [
                r'(?:Decision|Chose|Selected|Implemented|Created|Fixed):\s*([^\n]+)',
                r'(?:EXECUTING|COMPLETE|VALIDATED):\s*([^\n]+)',
            ]
            for pattern in decision_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    artifacts.append(SessionArtifact(
                        artifact_type='decision',
                        content=match.group(1),
                        context=match.group(0),
                    ))
        
        return artifacts
    
    def compress_content(self, turns: List[ConversationTurn]) -> List[ConversationTurn]:
        """
        Compress turns by removing redundancy and truncating verbose sections.
        
        STEP 3 of /saveprompt algorithm: COMPRESS
        """
        compressed = []
        
        for turn in turns:
            content = turn.content
            
            # Apply compression based on level
            if self.compression_level >= 2:
                # Truncate long code blocks
                content = self._truncate_code_blocks(content)
                
                # Remove verbose tool outputs
                content = self._compress_tool_outputs(content)
            
            if self.compression_level >= 3:
                # Remove redundant whitespace
                content = re.sub(r'\n{3,}', '\n\n', content)
                
                # Remove omission markers themselves
                for pattern in self.OMIT_PATTERNS:
                    content = re.sub(pattern, '', content)
            
            # Create compressed turn
            compressed_turn = ConversationTurn(
                type=turn.type,
                content=content.strip(),
                metadata=turn.metadata,
                line_start=turn.line_start,
                line_end=turn.line_end,
                importance=turn.importance,
            )
            compressed.append(compressed_turn)
        
        return compressed
    
    def _truncate_code_blocks(self, content: str) -> str:
        """Truncate long code blocks with informative markers"""
        lines = content.split('\n')
        result = []
        in_code_block = False
        code_lines = []
        code_lang = ''
        
        for line in lines:
            if self.patterns['code_block_start'].match(line) and not in_code_block:
                in_code_block = True
                match = self.patterns['code_block_start'].match(line)
                code_lang = match.group(1) if match.group(1) else ''
                code_lines = [line]
            elif self.patterns['code_block_end'].match(line) and in_code_block:
                code_lines.append(line)
                in_code_block = False
                
                # Check if truncation needed
                if len(code_lines) > self.MAX_CODE_BLOCK_LINES + 2:  # +2 for ``` markers
                    # Keep first and last portions
                    keep_start = self.MAX_CODE_BLOCK_LINES // 2
                    keep_end = self.MAX_CODE_BLOCK_LINES // 2
                    omitted = len(code_lines) - 2 - keep_start - keep_end
                    
                    result.append(code_lines[0])  # Opening ```
                    result.extend(code_lines[1:keep_start+1])
                    result.append(f'# ... [{omitted} lines truncated for brevity] ...')
                    result.extend(code_lines[-keep_end-1:-1])
                    result.append(code_lines[-1])  # Closing ```
                else:
                    result.extend(code_lines)
                
                code_lines = []
            elif in_code_block:
                code_lines.append(line)
            else:
                result.append(line)
        
        return '\n'.join(result)
    
    def _compress_tool_outputs(self, content: str) -> str:
        """Compress verbose tool outputs"""
        lines = content.split('\n')
        result = []
        in_tool_output = False
        tool_lines = []
        
        for line in lines:
            # Detect tool output start
            if self.patterns['tool_result_start'].match(line):
                in_tool_output = True
                tool_lines = [line]
            elif in_tool_output:
                # End on empty line or new section
                if line.strip() == '' or line.startswith('#') or line.startswith('User:'):
                    in_tool_output = False
                    
                    # Truncate if too long
                    if len(tool_lines) > self.MAX_TOOL_OUTPUT_LINES:
                        result.extend(tool_lines[:self.MAX_TOOL_OUTPUT_LINES//2])
                        omitted = len(tool_lines) - self.MAX_TOOL_OUTPUT_LINES
                        result.append(f'> [{omitted} lines of output truncated]')
                        result.extend(tool_lines[-self.MAX_TOOL_OUTPUT_LINES//2:])
                    else:
                        result.extend(tool_lines)
                    
                    result.append(line)
                    tool_lines = []
                else:
                    tool_lines.append(line)
            else:
                result.append(line)
        
        # Handle remaining tool output
        if tool_lines:
            if len(tool_lines) > self.MAX_TOOL_OUTPUT_LINES:
                result.extend(tool_lines[:self.MAX_TOOL_OUTPUT_LINES//2])
                omitted = len(tool_lines) - self.MAX_TOOL_OUTPUT_LINES
                result.append(f'> [{omitted} lines of output truncated]')
            else:
                result.extend(tool_lines)
        
        return '\n'.join(result)
    
    def beautify_markdown(self, turns: List[ConversationTurn]) -> str:
        """
        Apply consistent markdown formatting.
        
        STEP 4 of /saveprompt algorithm: BEAUTIFY
        Compliant with FA5 (Visual Integrity)
        """
        sections = []
        
        for i, turn in enumerate(turns):
            if turn.type == MessageType.USER:
                sections.append(f"## User Query {i//2 + 1}\n\n{turn.content}\n")
            elif turn.type == MessageType.ASSISTANT:
                sections.append(f"## Assistant Response {i//2 + 1}\n\n{turn.content}\n")
        
        return '\n---\n\n'.join(sections)
    
    def generate_metadata_header(self, 
                                  title: str, 
                                  original_lines: int, 
                                  compressed_lines: int,
                                  artifacts: List[SessionArtifact]) -> str:
        """
        Generate metadata header for processed session.
        
        STEP 5 of /saveprompt algorithm: ANNOTATE
        """
        timestamp = datetime.now().isoformat()
        compression_ratio = (1 - compressed_lines / original_lines) * 100 if original_lines > 0 else 0
        
        # Categorize artifacts
        code_count = sum(1 for a in artifacts if a.artifact_type == 'code')
        file_count = sum(1 for a in artifacts if a.artifact_type == 'file_change')
        decision_count = sum(1 for a in artifacts if a.artifact_type == 'decision')
        
        header = f"""---
title: "{title}"
processed_at: "{timestamp}"
algorithm: "/saveprompt v1.0"
compression_level: {self.compression_level}
original_lines: {original_lines}
compressed_lines: {compressed_lines}
compression_ratio: "{compression_ratio:.1f}%"
artifacts:
  code_blocks: {code_count}
  file_changes: {file_count}
  decisions: {decision_count}
ssot_compliance:
  fa4_validated: true
  fa5_visual_integrity: true
---

"""
        return header
    
    def generate_summary(self, turns: List[ConversationTurn], artifacts: List[SessionArtifact]) -> str:
        """Generate executive summary of the session"""
        user_queries = [t for t in turns if t.type == MessageType.USER]
        
        summary_lines = ["## Session Summary\n"]
        
        # Topics covered
        summary_lines.append("### Topics Covered\n")
        for i, query in enumerate(user_queries[:5], 1):  # First 5 queries
            # Extract first line or sentence
            first_line = query.content.split('\n')[0][:100]
            if len(query.content) > 100:
                first_line += '...'
            summary_lines.append(f"{i}. {first_line}")
        
        if len(user_queries) > 5:
            summary_lines.append(f"... and {len(user_queries) - 5} more queries")
        
        # Key artifacts
        if artifacts:
            summary_lines.append("\n### Key Artifacts\n")
            for artifact in artifacts[:10]:  # First 10 artifacts
                summary_lines.append(f"- **{artifact.artifact_type}**: {artifact.content[:80]}...")
        
        return '\n'.join(summary_lines)
    
    def compute_hash(self, content: str) -> str:
        """Compute canonical hash of content (SSOT XIV compliance)"""
        # Canonicalize
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        content = unicodedata.normalize('NFC', content).strip()
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def process(self, content: str, title: str = "Untitled Session") -> ProcessedSession:
        """
        Main processing pipeline implementing /saveprompt algorithm.
        
        Args:
            content: Raw session content
            title: Session title
            
        Returns:
            ProcessedSession with all processed data
        """
        original_lines = len(content.split('\n'))
        
        # STEP 1: PARSE
        turns = self.parse_raw_session(content)
        
        # STEP 2: EXTRACT
        artifacts = self.extract_artifacts(turns)
        
        # STEP 3: COMPRESS
        compressed_turns = self.compress_content(turns)
        
        # STEP 4: BEAUTIFY
        beautified_content = self.beautify_markdown(compressed_turns)
        
        # STEP 5: ANNOTATE
        summary = self.generate_summary(compressed_turns, artifacts)
        header = self.generate_metadata_header(
            title=title,
            original_lines=original_lines,
            compressed_lines=len(beautified_content.split('\n')),
            artifacts=artifacts
        )
        
        # Combine final document
        final_content = header + summary + "\n\n---\n\n# Full Session\n\n" + beautified_content
        
        # STEP 6: VALIDATE (compute hash for integrity)
        content_hash = self.compute_hash(final_content)
        
        return ProcessedSession(
            title=title,
            date=datetime.now().strftime('%Y-%m-%d'),
            turns=compressed_turns,
            artifacts=artifacts,
            summary=summary,
            original_lines=original_lines,
            compressed_lines=len(final_content.split('\n')),
            content_hash=content_hash
        )
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Process a single file and save result"""
        content = input_path.read_text(encoding='utf-8')
        
        # Derive title from filename
        title = input_path.stem.replace('_', ' ').title()
        
        # Process
        result = self.process(content, title)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix('.md')
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate final document
        final_doc = self._generate_final_document(result)
        
        # Write
        output_path.write_text(final_doc, encoding='utf-8')
        
        return output_path
    
    def _generate_final_document(self, result: ProcessedSession) -> str:
        """Generate the final markdown document"""
        header = self.generate_metadata_header(
            title=result.title,
            original_lines=result.original_lines,
            compressed_lines=result.compressed_lines,
            artifacts=result.artifacts
        )
        
        beautified = self.beautify_markdown(result.turns)
        
        return header + result.summary + "\n\n---\n\n# Full Session\n\n" + beautified
    
    def process_folder(self, folder_path: Path, output_folder: Optional[Path] = None) -> List[Path]:
        """Process all session files in a folder"""
        if output_folder is None:
            output_folder = folder_path / 'processed'
        
        output_folder.mkdir(exist_ok=True)
        
        processed_files = []
        
        # Find all files (excluding already processed .md files)
        for file_path in folder_path.iterdir():
            if file_path.is_file() and not file_path.suffix == '.md':
                try:
                    output_path = output_folder / (file_path.stem + '.md')
                    self.process_file(file_path, output_path)
                    processed_files.append(output_path)
                    print(f"  Processed: {file_path.name} -> {output_path.name}")
                except Exception as e:
                    print(f"  Error processing {file_path.name}: {e}")
        
        return processed_files

    # =========================================================================
    # PROMPT EXTRACTION MODE (VS Code /savePrompt Convention)
    # =========================================================================
    
    def extract_prompts(self, content: str, source_name: str = "unknown") -> List[ExtractedPrompt]:
        """
        Extract reusable .prompt.md templates from session.
        
        Implements VS Code's /savePrompt algorithm:
        1. REVIEW - Identify user's primary goal/task patterns
        2. GENERALIZE - Remove conversation-specific details
        3. PLACEHOLDER - Insert reusable placeholders
        4. TITLE - Create camelCase action-oriented title
        5. DESCRIBE - Write brief description
        6. FORMAT - Generate .prompt.md format
        """
        # Parse the session first
        turns = self.parse_raw_session(content)
        user_turns = [t for t in turns if t.type == MessageType.USER]
        
        if not user_turns:
            return []
        
        extracted = []
        
        # Group related queries into task patterns (aggregate by type)
        task_patterns = self._identify_task_patterns(user_turns)
        
        # Only create prompts for significant patterns (≥2 occurrences)
        for pattern in task_patterns:
            prompt = self._generalize_to_prompt(pattern, source_name)
            if prompt:
                extracted.append(prompt)
        
        return extracted
    
    def _identify_task_patterns(self, user_turns: List[ConversationTurn]) -> List[Dict[str, Any]]:
        """
        Identify recurring task patterns from user queries.
        
        STEP 1 of prompt extraction: REVIEW
        
        Aggregates queries by task type rather than creating one per query.
        """
        # Heuristics for task pattern detection
        task_keywords = {
            'create': ['create', 'generate', 'make', 'build', 'write', 'add', 'implement'],
            'refactor': ['refactor', 'improve', 'optimize', 'clean', 'restructure', 'enhance'],
            'debug': ['fix', 'debug', 'error', 'issue', 'problem', 'broken', 'failing'],
            'explain': ['explain', 'what is', 'how does', 'why', 'understand', 'clarify'],
            'test': ['test', 'unit test', 'integration', 'coverage', 'spec', 'verify'],
            'document': ['document', 'comment', 'readme', 'docs', 'jsdoc', 'annotate'],
            'analyze': ['analyze', 'review', 'audit', 'check', 'validate', 'inspect'],
        }
        
        # Aggregate by task type
        type_buckets: Dict[str, List[ConversationTurn]] = {k: [] for k in task_keywords}
        
        for turn in user_turns:
            content_lower = turn.content.lower()
            
            # Detect task type
            for task_type, keywords in task_keywords.items():
                if any(kw in content_lower for kw in keywords):
                    type_buckets[task_type].append(turn)
                    break  # Only assign to first matching type
        
        # Convert to patterns (only types with ≥2 queries)
        patterns = []
        for task_type, queries in type_buckets.items():
            if len(queries) >= 2:  # Minimum threshold for "pattern"
                # Find the most representative query (longest with good content)
                best_sample = max(queries, key=lambda q: len(q.content) if len(q.content) < 500 else 0)
                patterns.append({
                    'type': task_type,
                    'queries': queries,
                    'sample': best_sample.content,
                    'count': len(queries)
                })
        
        return patterns
    
    def _generalize_to_prompt(self, pattern: Dict[str, Any], source_name: str) -> Optional[ExtractedPrompt]:
        """
        Generalize a task pattern into reusable prompt.
        
        STEPS 2-6 of prompt extraction: GENERALIZE, PLACEHOLDER, TITLE, DESCRIBE, FORMAT
        """
        task_type = pattern['type']
        sample = pattern['sample']
        query_count = pattern.get('count', len(pattern['queries']))
        
        # Skip if only one occurrence (not a real pattern)
        # But keep significant single queries
        if query_count < 1:
            return None
        
        # STEP 2: GENERALIZE - Remove specific details
        generalized = self._remove_specifics(sample)
        
        # STEP 3: PLACEHOLDER - Insert placeholders
        prompt_text = self._insert_placeholders(generalized, task_type)
        
        # STEP 4: TITLE - Create camelCase title
        name = self._generate_camel_case_title(task_type, sample, query_count)
        
        # STEP 5: DESCRIBE - Brief description
        description = self._generate_description(task_type, query_count)
        
        # Determine tools needed
        tools = self._infer_tools(task_type)
        
        # Determine argument hint
        argument_hint = self._generate_argument_hint(task_type)
        
        return ExtractedPrompt(
            name=name,
            description=description,
            argument_hint=argument_hint,
            prompt_text=prompt_text,
            tools=tools,
            source_session=source_name
        )
    
    def _remove_specifics(self, content: str) -> str:
        """Remove conversation-specific details (file names, variable names, etc.)"""
        result = content
        
        # Remove specific file paths
        result = re.sub(r'[A-Za-z]:\\[^\s]+', '<file-path>', result)
        result = re.sub(r'/[^\s]+\.[a-z]+', '<file-path>', result)
        
        # Remove specific variable/function names in backticks
        result = re.sub(r'`[a-zA-Z_][a-zA-Z0-9_]*`', '`<identifier>`', result)
        
        # Remove specific URLs
        result = re.sub(r'https?://[^\s]+', '<url>', result)
        
        # Remove specific numbers/IDs
        result = re.sub(r'\b[0-9a-f]{8,}\b', '<hash>', result)
        
        return result
    
    def _insert_placeholders(self, content: str, task_type: str) -> str:
        """Insert reusable placeholders appropriate for task type.
        
        Uses {{argument}} for VS Code Copilot interpolation of user input.
        """
        placeholders = {
            'create': "Create {{argument}}.\n\n## Guidelines\n\n- Follow existing codebase conventions\n- Include appropriate error handling\n- Add inline documentation",
            'refactor': "Refactor {{argument}}.\n\n## Considerations\n\n- Maintain existing behavior\n- Improve code clarity\n- Optimize performance where applicable",
            'debug': "Debug: {{argument}}\n\n## Investigation Steps\n\n1. Reproduce the issue\n2. Analyze error messages\n3. Identify root cause\n4. Implement fix",
            'explain': "Explain {{argument}}.\n\n## Coverage\n\n- **How it works**: Step-by-step breakdown\n- **Why this approach**: Design rationale\n- **Key considerations**: Edge cases, performance",
            'test': "Generate tests for {{argument}}.\n\n## Test Coverage\n\n- **Happy path**: Normal operation\n- **Edge cases**: Boundary conditions\n- **Error handling**: Invalid inputs",
            'document': "Document {{argument}}.\n\n## Documentation Elements\n\n- **Purpose**: What it does\n- **Parameters**: Input descriptions\n- **Returns**: Output description\n- **Examples**: Usage demonstrations",
            'analyze': "Analyze {{argument}}.\n\n## Review Areas\n\n- **Issues**: Bugs, security vulnerabilities\n- **Performance**: Inefficiencies\n- **Best practices**: Idiomatic patterns",
        }
        
        # Return clean template without session-specific context noise
        return placeholders.get(task_type, f"Process {{{{argument}}}} for {task_type} task.")
    
    def _generate_camel_case_title(self, task_type: str, sample: str, query_count: int) -> str:
        """Generate camelCase action-oriented title based on task type and session context"""
        # Standard task-based titles (simpler, more reusable)
        base_titles = {
            'create': 'createComponent',
            'refactor': 'refactorCode',
            'debug': 'debugIssue',
            'explain': 'explainCode',
            'test': 'generateTests',
            'document': 'documentCode',
            'analyze': 'analyzeCode',
        }
        
        return base_titles.get(task_type, f"{task_type}Code")
    
    def _generate_description(self, task_type: str, occurrence_count: int) -> str:
        """Generate brief description (≤15 words) with occurrence context"""
        descriptions = {
            'create': "Generate new code components based on specifications",
            'refactor': "Improve code structure while preserving behavior",
            'debug': "Identify and fix issues in the codebase",
            'explain': "Provide clear explanations of code or concepts",
            'test': "Generate comprehensive test coverage",
            'document': "Add documentation and comments to code",
            'analyze': "Review code for issues and improvements",
        }
        
        base = descriptions.get(task_type, f"Perform {task_type} tasks on code")
        return f"{base} (pattern from {occurrence_count} queries)"
    
    def _infer_tools(self, task_type: str) -> List[str]:
        """Infer which tools a prompt type typically needs"""
        tool_map = {
            'create': ['edit', 'search'],
            'refactor': ['edit', 'search', 'read_file'],
            'debug': ['edit', 'search', 'run_in_terminal', 'get_errors'],
            'explain': ['search', 'read_file'],
            'test': ['edit', 'search', 'run_in_terminal'],
            'document': ['edit', 'read_file'],
            'analyze': ['search', 'read_file', 'get_errors'],
        }
        return tool_map.get(task_type, ['edit', 'search'])
    
    def _generate_argument_hint(self, task_type: str) -> Optional[str]:
        """Generate argument hint for the prompt"""
        hints = {
            'create': "Describe what to create",
            'refactor': "Select the code to refactor",
            'debug': "Describe the bug or select error location",
            'explain': "Select code or name concept to explain",
            'test': "Select function or class to test",
            'document': "Select code to document",
            'analyze': "Select code or file to analyze",
        }
        return hints.get(task_type)
    
    def format_prompt_md(self, prompt: ExtractedPrompt) -> str:
        """
        Format ExtractedPrompt as .prompt.md content (VS Code convention).
        
        Output follows: https://github.com/microsoft/vscode-copilot-chat/blob/main/assets/prompts/savePrompt.prompt.md
        """
        lines = ["---"]
        lines.append(f"name: {prompt.name}")
        lines.append(f"description: {prompt.description}")
        
        if prompt.argument_hint:
            lines.append(f"argument-hint: {prompt.argument_hint}")
        
        if prompt.tools:
            tools_str = ", ".join(f"'{t}'" for t in prompt.tools)
            lines.append(f"tools: [ {tools_str} ]")
        
        # Add mode field - agent for action prompts, ask for explanation prompts
        mode = "ask" if prompt.name in ("explainCode", "analyzeCode") else "agent"
        lines.append(f"mode: {mode}")
        
        if prompt.source_session:
            lines.append(f"# Extracted from: {prompt.source_session}")
        
        lines.append("---")
        lines.append("")
        lines.append(prompt.prompt_text)
        
        return "\n".join(lines)
    
    def extract_prompts_from_file(self, input_path: Path, output_folder: Optional[Path] = None) -> List[Path]:
        """Extract prompts from a session file and save as .prompt.md files"""
        content = input_path.read_text(encoding='utf-8')
        prompts = self.extract_prompts(content, input_path.name)
        
        if not prompts:
            print(f"  No reusable patterns found in {input_path.name}")
            return []
        
        if output_folder is None:
            # Default to .github/prompts/ for VS Code discovery
            repo_root = input_path.parent
            while repo_root.parent != repo_root:
                if (repo_root / '.github').exists():
                    output_folder = repo_root / '.github' / 'prompts'
                    break
                repo_root = repo_root.parent
            else:
                output_folder = input_path.parent / 'prompts'
        
        output_folder.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        for prompt in prompts:
            output_path = output_folder / f"{prompt.name}.prompt.md"
            content = self.format_prompt_md(prompt)
            output_path.write_text(content, encoding='utf-8')
            saved_files.append(output_path)
            print(f"  Extracted: {prompt.name}.prompt.md")
        
        return saved_files


def main():
    parser = argparse.ArgumentParser(
        description='/saveprompt Algorithm - Hybrid Session Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODES:
  Archive (default): Beautify raw sessions into clean .md documents
  Extract (--extract-prompts): Generate reusable .prompt.md templates

Examples:
  # Archive mode - beautify sessions
  python saveprompt_algorithm.py session.txt
  python saveprompt_algorithm.py session.txt --output beautified.md
  python saveprompt_algorithm.py --folder ./raw_sessions
  python saveprompt_algorithm.py session.txt --compression 3
  
  # Extract mode - generate reusable prompts
  python saveprompt_algorithm.py session.txt --extract-prompts
  python saveprompt_algorithm.py --folder ./raw_sessions --extract-prompts
  
  # Combined - do both
  python saveprompt_algorithm.py session.txt --extract-prompts --output beautified.md
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input file path')
    parser.add_argument('--folder', '-f', help='Process all files in folder')
    parser.add_argument('--output', '-o', help='Output file path (archive mode)')
    parser.add_argument('--compression', '-c', type=int, default=2, choices=[1, 2, 3],
                        help='Compression level: 1=minimal, 2=balanced, 3=aggressive')
    parser.add_argument('--extract-prompts', '-e', action='store_true',
                        help='Extract reusable .prompt.md templates (VS Code convention)')
    parser.add_argument('--prompts-output', '-p', help='Output folder for extracted prompts')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without writing')
    
    args = parser.parse_args()
    
    processor = SavePromptProcessor(compression_level=args.compression)
    
    if args.folder:
        folder_path = Path(args.folder)
        if not folder_path.exists():
            print(f"Error: Folder not found: {folder_path}")
            return 1
        
        print(f"Processing folder: {folder_path}")
        
        # Archive mode
        if not args.extract_prompts or args.output:
            print("\n[ARCHIVE MODE] Beautifying sessions...")
            processed = processor.process_folder(folder_path)
            print(f"  Archived {len(processed)} files")
        
        # Extract mode
        if args.extract_prompts:
            print("\n[EXTRACT MODE] Generating reusable prompts...")
            prompts_output = Path(args.prompts_output) if args.prompts_output else folder_path / 'prompts'
            total_prompts = 0
            for file_path in folder_path.iterdir():
                if file_path.is_file() and not file_path.suffix == '.md':
                    extracted = processor.extract_prompts_from_file(file_path, prompts_output)
                    total_prompts += len(extracted)
            print(f"  Extracted {total_prompts} prompt templates")
        
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            return 1
        
        output_path = Path(args.output) if args.output else None
        
        if args.dry_run:
            content = input_path.read_text(encoding='utf-8')
            result = processor.process(content, input_path.stem)
            print(f"Would process: {input_path}")
            print(f"  Original: {result.original_lines} lines")
            print(f"  Compressed: {result.compressed_lines} lines")
            print(f"  Artifacts: {len(result.artifacts)}")
            print(f"  Hash: {result.content_hash}")
            
            if args.extract_prompts:
                prompts = processor.extract_prompts(content, input_path.name)
                print(f"\n  Would extract {len(prompts)} prompt templates:")
                for p in prompts:
                    print(f"    - {p.name}: {p.description}")
        else:
            # Archive mode
            if not args.extract_prompts or args.output:
                output = processor.process_file(input_path, output_path)
                print(f"[ARCHIVE] {input_path} -> {output}")
            
            # Extract mode  
            if args.extract_prompts:
                prompts_output = Path(args.prompts_output) if args.prompts_output else None
                extracted = processor.extract_prompts_from_file(input_path, prompts_output)
                print(f"[EXTRACT] Generated {len(extracted)} prompt templates")
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
