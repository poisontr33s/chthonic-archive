# Ruby 4.0.3 Win32 Native Build — Patch Status

## Root cause
`c_ulong = u32` on Windows (vs `u64` on Linux x86-64). YJIT/ZJIT Rust code assumes Linux ABI.

## Patch files needed
1. jit.c (already patched via patch-jit-win32.py) — ICE fix still needed at line 727
2. yjit/src/cruby.rs — 3 changes (str.len as i64, def_ids store cast, ID! macro cast)
3. zjit/src/cruby.rs — 2 changes (def_ids store .0 as u64, ID! macro ID(id as _))
4. yjit/src/disasm.rs — fd→handle, c_long casts (6 changes)
5. yjit/src/options.rs — RawFd enum variants + IntoRawFd (6 changes)
6. yjit/src/log.rs — FromRawFd/IntoRawFd (4 changes)
7. yjit/src/codegen.rs — ivar_name type, Opnd::UImm widening, RSTRUCT_LEN, rb_hash, get_method_name (12 changes)
8. zjit/src/hir.rs — map_id widening, yarv_ary_entry, include_p comparison, ID(as_u64 as _) x7 (10 changes)
9. zjit/src/codegen.rs — Opnd::Imm(cap.into()) (1 change)

## Key discoveries
- yjit: `pub type ID = c_ulong` (type alias in cruby_bindings.inc.rs line 175)
- zjit: `pub struct ID(pub c_ulong)` (newtype in cruby.rs line 256)
- Both: AtomicU64 stores IDs, but on Windows load returns u64 that must fit in u32
- Macro fix cascades to fix ~60% of errors
- fd→handle: enum variants in options.rs, usage in disasm.rs/log.rs need cfg guards
- ivar_name: jit.get_arg(0).as_u64() returns u64, must type as ID for function args
  then Opnd::UImm(ivar_name as u64) for widening back
- RSTRUCT_LEN returns c_long = i32 on Windows (was i64 Linux)
- rb_hash_new_with_size takes st_index_t = c_ulong = u32 on Windows

## ivar_name fix pattern
- Lines 3004, 3067, 3366: `let ivar_name = jit.get_arg(0).as_u64();`
  → `let ivar_name: ID = jit.get_arg(0).as_u64() as _;` (this is u64 as u32 on Win)
  But then Opnd::UImm(ivar_name) needs widening: → Opnd::UImm(ivar_name as u64)

## Patch script location
C:\Users\eldno\chthonic-archive\build\ruby-zjit\patch-rust-win32.py (TO CREATE)

## Source location
/tmp/ruby-zjit-linux/ (WSL2) AND C:\ruby-zjit-build\ruby-4.0.3\ (Windows)
Apply patches to C:\ruby-zjit-build\ruby-4.0.3\
