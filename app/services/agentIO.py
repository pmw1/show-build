from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import os
import shutil
import re

router = APIRouter()

class WritePayload(BaseModel):
    path: str
    content: str
    permissions: str | None = None
    owner: str | None = None
    group: str | None = None
    overwrite: bool = False

class PatchPayload(BaseModel):
    path: str
    target: str
    replacement: str

@router.get("/ls")
def list_directory(path: str):
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    return {"entries": sorted([entry.name for entry in p.iterdir()])}

@router.get("/tree")
def directory_tree(path: str, depth: int = 2):
    base = Path(path)
    if not base.exists() or not base.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    def walk(p: Path, current_depth: int):
        if current_depth < 0:
            return None
        if p.is_dir():
            entries = list(p.iterdir())
            return {
                "type": "directory",
                "name": p.name,
                "num_files": sum(1 for e in entries if e.is_file()),
                "num_dirs": sum(1 for e in entries if e.is_dir()),
                "children": [walk(child, current_depth - 1) for child in sorted(entries) if walk(child, current_depth - 1) is not None]
            }
        else:
            return {"type": "file", "name": p.name}

    return walk(base, depth)

@router.get("/read")
def read_file(path: str):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = p.read_text()
        return {"path": str(p), "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/write")
def write_file(payload: WritePayload):
    p = Path(payload.path)
    if p.exists() and not payload.overwrite:
        raise HTTPException(status_code=409, detail="File already exists")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(payload.content)
        if payload.permissions:
            os.chmod(p, int(payload.permissions, 8))
        if payload.owner or payload.group:
            uid = shutil._get_uid(payload.owner) if payload.owner else -1
            gid = shutil._get_gid(payload.group) if payload.group else -1
            os.chown(p, uid, gid)
        return {"status": "success", "path": str(p)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info", response_class=HTMLResponse)
def info():
    html_content = """
    <html>
      <head><title>AgentIO API Info</title></head>
      <body>
        <h1>AgentIO API Endpoints</h1>
        <ul>
          <li><strong>GET /ls?path=&lt;directory&gt;</strong><br>List files and directories.</li>
          <li><strong>GET /tree?path=&lt;directory&gt;&amp;depth=2</strong><br>View recursive directory tree structure. Includes number of sub-files and sub-directories per folder.</li>
          <li><strong>GET /read?path=&lt;file_path&gt;</strong><br>Read file contents.</li>
          <li><strong>POST /write</strong><br>Write or overwrite a file. JSON payload:<br>
            <pre>{
  "path": "/path/to/file",
  "content": "...",
  "permissions": "644",
  "owner": "user",
  "group": "group",
  "overwrite": true
}</pre>
          </li>
          <li><strong>GET /code/get_block?path=&lt;file&gt;&block_name=&lt;function_or_class&gt;</strong><br>Extract a named function or class block.</li>
          <li><strong>POST /code/patch_block</strong><br>Replace a block with new content. JSON payload:<br>
            <pre>{
  "path": "/app/main.py",
  "target": "def old_func(...): ...",
  "replacement": "def new_func(...): ..."
}</pre>
          </li>
        </ul>
      </body>
    </html>
    """
    return html_content

@router.get("/code/get_block")
def get_code_block(path: str, block_name: str):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        code = p.read_text()
        pattern = rf"^(def|class)\s+{re.escape(block_name)}\b.*?(?=^\S|\Z)"
        match = re.search(pattern, code, re.DOTALL | re.MULTILINE)
        if not match:
            raise HTTPException(status_code=404, detail="Block not found")
        return {"block": match.group(0)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/code/patch_block")
def patch_code_block(payload: PatchPayload):
    p = Path(payload.path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        code = p.read_text()
        if payload.target not in code:
            raise HTTPException(status_code=400, detail="Target block not found in file")
        updated = code.replace(payload.target, payload.replacement)
        p.write_text(updated)
        return {"status": "patched", "path": str(p)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

