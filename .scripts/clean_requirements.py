from pathlib import Path
p=Path('app/rag/requirements-retriever.txt')
if not p.exists():
    print('file not found:', p)
    raise SystemExit(1)
b=p.read_bytes()
backup=p.with_suffix('.txt.bak')
backup.write_bytes(b)
clean=b.replace(b'\x00', b'')
p.write_bytes(clean)
print('original_bytes=', len(b), 'clean_bytes=', len(clean), 'nul_removed=', b.count(b'\x00'))
