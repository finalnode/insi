"""Reproduzierbare Codefingerprints für Ähnlichkeitshinweise."""

import ast
import builtins
import hashlib
import re
from dataclasses import asdict, dataclass

ALGORITHM = "insi-python-ast-v1"
PYTHON_NAMES = frozenset(dir(builtins))


@dataclass(frozen=True)
class CodeFingerprints:
    algorithm: str
    exact_sha256: str
    canonical_sha256: str
    structural_sha256: str | None
    syntax_valid: bool

    def as_dict(self) -> dict[str, str | bool | None]:
        return asdict(self)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _exact_source(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n")


def _text_fallback(source: str) -> str:
    lines = []
    for line in _exact_source(source).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(re.sub(r"\s+", " ", stripped))
    return "\n".join(lines)


class _AlphaRenamer(ast.NodeTransformer):
    """Ersetze selbst gebundene Namen pro Gültigkeitsbereich deterministisch."""

    def __init__(self, protected_names: frozenset[str]) -> None:
        self.scopes: list[dict[str, str]] = [{}]
        self.protected_names = PYTHON_NAMES | protected_names

    @staticmethod
    def _label(index: int) -> str:
        result = ""
        number = index
        while True:
            number, remainder = divmod(number, 26)
            result = chr(ord("a") + remainder) + result
            if number == 0:
                return result
            number -= 1

    def _bind(self, name: str) -> str:
        if name in self.protected_names:
            return name
        scope = self.scopes[-1]
        if name not in scope:
            scope[name] = self._label(len(scope))
        return scope[name]

    def _lookup(self, name: str) -> str:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return name

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self._bind(node.id) if isinstance(node.ctx, ast.Store) else self._lookup(node.id)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._bind(node.arg)
        return node

    def visit_alias(self, node: ast.alias) -> ast.alias:
        if node.asname:
            node.asname = self._bind(node.asname)
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        node.type = self.visit(node.type) if node.type else None
        if node.name:
            node.name = self._bind(node.name)
        node.body = [self.visit(item) for item in node.body]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = self._bind(node.name)
        node.decorator_list = [self.visit(item) for item in node.decorator_list]
        node.returns = self.visit(node.returns) if node.returns else None
        self.scopes.append({})
        node.args = self.visit(node.args)
        node.body = [self.visit(item) for item in node.body]
        self.scopes.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> ast.AST:
        self.scopes.append({})
        node.args = self.visit(node.args)
        node.body = self.visit(node.body)
        self.scopes.pop()
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        node.name = self._bind(node.name)
        node.bases = [self.visit(item) for item in node.bases]
        node.keywords = [self.visit(item) for item in node.keywords]
        self.scopes.append({})
        node.body = [self.visit(item) for item in node.body]
        self.scopes.pop()
        return node


def code_fingerprints(
    source: str,
    *,
    protected_names: frozenset[str] = frozenset(),
    algorithm: str = ALGORITHM,
) -> CodeFingerprints:
    """Bilde exakten, formatierten und alpha-normalisierten SHA-256-Hash."""
    exact = _exact_source(source)
    try:
        tree = ast.parse(exact)
    except SyntaxError:
        fallback = _text_fallback(exact)
        return CodeFingerprints(algorithm, _hash(exact), _hash(fallback), None, False)

    canonical = ast.unparse(tree)
    structural_tree = _AlphaRenamer(protected_names).visit(ast.parse(exact))
    ast.fix_missing_locations(structural_tree)
    structural = ast.dump(structural_tree, include_attributes=False)
    return CodeFingerprints(
        algorithm,
        _hash(exact),
        _hash(canonical),
        _hash(structural),
        True,
    )
