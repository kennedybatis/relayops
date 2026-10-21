const $ = (id) => document.getElementById(id);
function el(tag, text, className) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (className) n.className = className;
  return n;
}
const labels = {
  sales_ready: "Pronto para vendas",
  needs_information: "Faltam informações",
  nurture: "Nutrição",
  duplicate: "Duplicado",
  no_contact: "Sem permissão",
};
async function request(path, body) {
  const r = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  if (!r.ok)
    throw Error(
      "A operação falhou. Confira o estado antes de tentar novamente.",
    );
  return r.json();
}
async function refresh() {
  const s = await request("/api/state");
  $("metrics").replaceChildren();
  const cards = [
    ["Leads processados", s.runs.length, "Entradas únicas por ID"],
    [
      "Prontos para vendas",
      s.runs.filter((r) => r.status === "sales_ready").length,
      "Critérios explícitos",
    ],
    [
      "Aguardam aprovação",
      s.approvals.filter((a) => a.status === "pending").length,
      "Nenhum envio automático",
    ],
    [
      "Eventos auditáveis",
      s.audit_events,
      s.audit_valid ? "Cadeia de hashes íntegra" : "Falha de integridade",
    ],
  ];
  for (const [label, value, note] of cards) {
    const card = el("div", undefined, "metric");
    card.append(
      el("span", label),
      el("strong", String(value)),
      el("small", note),
    );
    $("metrics").append(card);
  }
  $("runs").replaceChildren();
  for (const r of s.runs) {
    const row = el("tr");
    const status = el("td");
    status.append(el("span", labels[r.status] || r.status, "pill"));
    row.append(
      el("td", r.name),
      status,
      el("td", r.reason),
      el("td", r.elapsed_ms + " ms"),
    );
    $("runs").append(row);
  }
  if (!s.runs.length) {
    const row = el("tr");
    const cell = el(
      "td",
      "Execute a demonstração para inspecionar seis cenários.",
    );
    cell.colSpan = 4;
    row.append(cell);
    $("runs").append(row);
  }
  $("approvals").replaceChildren();
  for (const a of s.approvals) {
    const box = el("article", undefined, "approval");
    box.append(
      el("h3", a.payload.lead_id + " / " + a.status),
      el("p", a.payload.to, "recipient"),
      el("p", a.payload.body),
    );
    if (a.status === "pending") {
      for (const [label, value, cls] of [
        ["Aprovar rascunho", "approved", ""],
        ["Rejeitar", "rejected", "reject"],
      ]) {
        const b = el("button", label, cls);
        b.onclick = async () => {
          b.disabled = true;
          try {
            await request("/api/decision", { id: a.id, decision: value });
            await refresh();
          } catch (e) {
            $("error").textContent = e.message;
            b.disabled = false;
          }
        };
        box.append(b);
      }
    }
    $("approvals").append(box);
  }
  $("audit").textContent =
    (s.audit_valid ? "✓ Auditoria íntegra" : "✗ Auditoria inválida") +
    " · " +
    s.outbox_count +
    " rascunhos liberados · 0 e-mails enviados";
}
$("run").onclick = async () => {
  $("run").disabled = true;
  $("error").textContent = "";
  try {
    await request("/api/demo", {});
    await refresh();
  } catch (e) {
    $("error").textContent = e.message;
  } finally {
    $("run").disabled = false;
  }
};
refresh().catch((e) => ($("error").textContent = e.message));
