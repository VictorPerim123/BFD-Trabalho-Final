import html as html_lib
import json
from datetime import datetime, timezone

from flask import Blueprint, Response

from app.services.backlog_service import BacklogService
from app.utils.auth import login_required, usuario_atual

export_bp = Blueprint("export", __name__)


@export_bp.route("/backlog/exportar")
@login_required
def exportar_backlog():
    usuario = usuario_atual()
    servico = BacklogService(usuario)
    jogos = [jogo.to_dict() for jogo in servico.listar_jogos()]
    gerado_em = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    html = _montar_html_standalone(usuario.nome, jogos, gerado_em)

    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition": "attachment; filename=backlog-savepoint.html"},
    )


def _montar_html_standalone(nome_usuario, jogos, gerado_em):
    nome_usuario = html_lib.escape(nome_usuario)
    dados_json = json.dumps(jogos, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Backlog SavePoint — {nome_usuario}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; background:#14121f; color:#f4f2fa; font-family: Inter, "Segoe UI", sans-serif; padding: 2rem; }}
  h1 {{ font-family: "Space Grotesk", sans-serif; }}
  .meta {{ color:#a8a3bd; font-size:0.85rem; margin-bottom:1.5rem; }}
  input[type=search] {{
    width:100%; max-width:320px; padding:0.6rem 0.9rem; margin-bottom:1.5rem;
    background:#1e1b2e; border:1px solid #3a3552; border-radius:6px; color:#f4f2fa;
  }}
  table {{ width:100%; border-collapse: collapse; }}
  th, td {{ text-align:left; padding:0.6rem 0.8rem; border-bottom:1px solid #3a3552; }}
  th {{ color:#a8a3bd; font-weight:600; font-size:0.8rem; text-transform:uppercase; }}
  .badge {{
    display:inline-block; padding:0.15rem 0.55rem; border-radius:999px; font-size:0.7rem;
    font-weight:700; text-transform:uppercase; border:1px solid #3a3552; color:#a8a3bd;
  }}
  .empty {{ color:#a8a3bd; padding: 2rem 0; }}
  footer {{ margin-top:2rem; font-size:0.75rem; color:#746e8f; }}
</style>
</head>
<body>
  <h1>Backlog de {nome_usuario}</h1>
  <p class="meta">Exportado do SavePoint em {gerado_em} — arquivo estático, funciona offline.</p>

  <input type="search" id="busca" placeholder="Buscar jogo…" aria-label="Buscar jogo no backlog exportado">

  <table>
    <thead>
      <tr><th>Título</th><th>Status</th><th>Nota</th><th>Horas</th><th>Conquistas</th><th>Categorias</th></tr>
    </thead>
    <tbody id="corpo-tabela"></tbody>
  </table>
  <p class="empty" id="vazio" hidden>Nenhum jogo encontrado.</p>

  <footer>Gerado automaticamente pelo SavePoint — este arquivo não se conecta a nenhum servidor.</footer>

<script>
  var jogos = {dados_json};

  function escapeHtml(valor) {{
    var div = document.createElement("div");
    div.textContent = valor == null ? "" : valor;
    return div.innerHTML;
  }}

  function renderizar(lista) {{
    var corpo = document.getElementById("corpo-tabela");
    var vazio = document.getElementById("vazio");
    corpo.innerHTML = "";

    if (lista.length === 0) {{
      vazio.hidden = false;
      return;
    }}
    vazio.hidden = true;

    lista.forEach(function (jogo) {{
      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" + escapeHtml(jogo.titulo) + "</td>" +
        "<td><span class=\\"badge\\">" + escapeHtml(jogo.status) + "</span></td>" +
        "<td>" + (jogo.nota != null ? jogo.nota : "—") + "</td>" +
        "<td>" + jogo.tempo_jogado_horas + "h</td>" +
        "<td>" + jogo.conquistas_obtidas + "/" + jogo.total_conquistas + " (" + jogo.percentual_conquistas + "%)</td>" +
        "<td>" + escapeHtml((jogo.categorias || []).join(", ")) + "</td>";
      corpo.appendChild(tr);
    }});
  }}

  document.getElementById("busca").addEventListener("input", function (evento) {{
    var termo = evento.target.value.trim().toLowerCase();
    var filtrados = jogos.filter(function (jogo) {{
      return jogo.titulo.toLowerCase().indexOf(termo) !== -1;
    }});
    renderizar(filtrados);
  }});

  renderizar(jogos);
</script>
</body>
</html>
"""
