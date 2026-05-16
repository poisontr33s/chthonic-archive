#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Patch Claude Code 2.1.143 webview bundle — replace stream-fatal throws with log+return
# SID: PATCH_CLAUDE_WEBVIEW_2143
import pathlib

ext = pathlib.Path(
    r"C:\Users\eldno\.vscode-insiders\extensions"
    r"\anthropic.claude-code-2.1.143-win32-x64\webview\index.js"
)
backup = ext.with_suffix(".js.bak-2.1.143")

content = ext.read_text(encoding="utf-8")

if not backup.exists():
    backup.write_text(content, encoding="utf-8")
    print(f"backup: {backup}")
else:
    print(f"backup already exists (skipping): {backup}")

patches = [
    # h20: text_delta mismatch
    (
        'if($.type!=="text")throw Error(`Mismatched content block type ${Z.type} ${$.type}`);$.text+=J.text',
        'if($.type!=="text"){try{console.warn("[patched-local] Mismatched text_delta:",Z.type,$.type)}catch(e){}return};$.text+=J.text',
    ),
    # h20: input_json_delta mismatch (inline else branch)
    (
        'else throw Error(`Mismatched content block type ${Z.type} ${$.type}`);break;case"thinking_delta"',
        'else{try{console.warn("[patched-local] Mismatched input_json_delta:",Z.type,$.type)}catch(e){}return};break;case"thinking_delta"',
    ),
    # h20: thinking_delta mismatch
    (
        'if($.type!=="thinking")throw Error(`Mismatched content block type ${Z.type} ${$.type}`);$.thinking+=J.thinking',
        'if($.type!=="thinking"){try{console.warn("[patched-local] Mismatched thinking_delta:",Z.type,$.type)}catch(e){}return};$.thinking+=J.thinking',
    ),
    # h20: signature_delta mismatch
    (
        'if($.type!=="thinking")throw Error(`Mismatched content block type ${Z.type} ${$.type}`);$.signature=J.signature',
        'if($.type!=="thinking"){try{console.warn("[patched-local] Mismatched signature_delta:",Z.type,$.type)}catch(e){}return};$.signature=J.signature',
    ),
    # qB1.processStreamEvent: content_block_delta without message
    (
        'if(!this.currentMessage)throw Error("Received content_block_delta without a current message")',
        'if(!this.currentMessage){try{console.warn("[patched-local] content_block_delta without message")}catch(e){}return}',
    ),
    # qB1.processStreamEvent: message_stop without message
    (
        'if(!this.currentMessage)throw Error("Received message_stop without a current message")',
        'if(!this.currentMessage){try{console.warn("[patched-local] message_stop without message")}catch(e){}return}',
    ),
]

patched = content
applied = 0
for old, new in patches:
    count = patched.count(old)
    if count == 1:
        patched = patched.replace(old, new)
        print(f"  PATCHED (1): {old[:70]}...")
        applied += 1
    elif count == 0:
        print(f"  SKIP   (0): {old[:70]}...")
    else:
        print(f"  WARN ({count}): {old[:70]}...")

remaining = patched.count("throw Error(`Mismatched content block type")
print(f"\nRemaining 'Mismatched' throws: {remaining}")
print(f"Applied: {applied}/{len(patches)}")

if applied > 0 and patched != content:
    ext.write_text(patched, encoding="utf-8")
    print(f"WRITTEN: {ext}")
else:
    print("No changes written.")
