"""notes-search 命令行入口。

核心层交付物 #1：先让 `notes-search --help` 能跑起来。

命令规划（按交付阶段）：
  parse   —— 核心层：只验证解析与分块，不碰数据库
  ingest  —— 核心层：解析 → 分块 → 建 FTS5 索引
  search  —— 核心层：查询
  stats   —— 差异化层：检索日志分析（SQL 练习场）
  serve   —— 主体层：起 FastAPI 服务
"""

from __future__ import annotations

from pathlib import Path

import typer

from . import __version__

app = typer.Typer(
    name="notes-search",
    help="个人讲义库的中文全文检索 + 语义检索服务。",
    add_completion=False,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"notes-search {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=_version_callback, is_eager=True, help="显示版本号"
    ),
) -> None:
    """notes-search：把一学期的讲义变成可检索的知识库。"""


@app.command()
def parse(
    path: Path = typer.Argument(..., help="文件或目录路径", exists=True),
    chunk_size: int = typer.Option(400, help="目标块大小（字符）"),
    overlap: int = typer.Option(40, help="相邻块重叠字符数"),
    limit: int = typer.Option(3, help="只显示前 N 个文件的解析结果"),
) -> None:
    """【第一步】只做解析 + 分块，看看效果，不写数据库。

    这是开发期最有用的命令：能在写数据库之前确认中文抽取质量。
    """
    from .chunk import chunk_pages
    from .parse import iter_supported_files, parse_file

    files = iter_supported_files(path)
    if not files:
        typer.secho("没有找到支持的文件（.pdf / .md / .txt）", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    typer.secho(f"找到 {len(files)} 个文件", fg=typer.colors.CYAN)

    total_chunks = 0
    for i, f in enumerate(files):
        try:
            doc = parse_file(f)
        except Exception as e:  # noqa: BLE001 — 单个文件失败不应该中断整批
            typer.secho(f"  ✗ {f.name}: {e}", fg=typer.colors.RED)
            continue

        chunks = chunk_pages(doc.pages, chunk_size=chunk_size, overlap=overlap)
        total_chunks += len(chunks)

        status = "✓" if doc.pages else "!"
        color = typer.colors.GREEN if doc.pages else typer.colors.YELLOW
        typer.secho(
            f"  {status} {f.name}: {len(doc.pages)} 页/块 → {len(chunks)} chunks, "
            f"{doc.char_count} 字符",
            fg=color,
        )

        if i < limit and chunks:
            sample = chunks[0].text.replace("\n", " ")[:100]
            typer.echo(f"      首块预览: {sample}...")

    typer.secho(f"\n合计 {total_chunks} 个 chunks", fg=typer.colors.CYAN)


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="文件或目录路径", exists=True),
    course: str = typer.Option(None, "--course", "-c", help="课程代号，如 CS3402"),
) -> None:
    """【核心层】解析 → 分块 → 写入 SQLite FTS5 索引。"""
    typer.secho("ingest 尚未实现（核心层交付物 #4）", fg=typer.colors.YELLOW)
    typer.echo("  下一步：实现 src/notes_search/store.py 的建表 + CJK 切分 + FTS5 导入")
    raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="查询词（中文自然语言）"),
    top: int = typer.Option(10, "--top", "-k", help="返回条数"),
    mode: str = typer.Option("bm25", "--mode", "-m", help="检索模式：bm25 / vector / hybrid"),
) -> None:
    """【核心层】检索。"""
    typer.secho("search 尚未实现（核心层交付物 #4）", fg=typer.colors.YELLOW)
    raise typer.Exit(code=1)


@app.command()
def stats() -> None:
    """【差异化层】检索日志分析：零结果查询 / 慢查询。"""
    typer.secho("stats 尚未实现（差异化层）", fg=typer.colors.YELLOW)
    raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="监听地址"),
    port: int = typer.Option(8000, help="监听端口"),
) -> None:
    """【主体层】启动 FastAPI 服务。"""
    typer.secho("serve 尚未实现（主体层交付物 #9）", fg=typer.colors.YELLOW)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
