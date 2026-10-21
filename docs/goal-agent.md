# Agente orientado por objetivo

O modo `demo` continua determinístico e sem dependências. O modo de revisão conectado usa um **LLM real no Ollama** para escolher ações, interpretar mensagens e escrever análises no Google Sheets. Regras de permissão e validações continuam no código.

## Objetivo de exemplo

> Revise os leads novos, registre a análise e a próxima ação no CRM, sinalize conflitos e confira cada gravação. Não envie mensagens.

## Ferramentas que o modelo pode escolher

| Ferramenta | Capacidade e condição |
|---|---|
| `read_campaign` | Carrega skill e referência da campanha |
| `read_leads` | Lê somente `Leads!A1:G11`; valida campos e IDs |
| `record_assessment` | Escreve uma revisão para um ID lido, em uma linha de `AgentReview` |
| `verify_record` | Lê a linha gravada e confere cada campo e a versão da origem |
| `finish` | Disponível depois da verificação de todos os registros; atualiza a conferência antes de concluir |

O runtime oferece apenas ferramentas válidas no estágio atual. O modelo escolhe a ordem de análise, redige o resumo, propõe a ação e identifica contradições. O código conserva orçamento e consentimento originais, aplica critérios explícitos e sinaliza `needs_review` quando o modelo identifica conflito. A interpretação é feita em uma chamada isolada por lead, separada da escolha da ferramenta. O resumo canônico é extrativo: um trecho literal da mensagem selecionado pelo modelo e validado contra a origem. O texto não ganha autoridade por estar no prompt. O modelo também pode citar um valor monetário literal da mensagem; o runtime verifica a citação, interpreta os formatos monetários suportados e compara com o orçamento cadastrado. Divergências ou múltiplos valores monetários em mensagens sobre orçamento sinalizam revisão mesmo se o modelo errar a flag ou selecionar o valor rejeitado pelo cliente. Isso é um gatilho conservador de esclarecimento, não uma afirmação de que cada valor citado é orçamento disponível. A seleção de trechos relevantes e conflitos fora desses formatos ainda dependem da qualidade do modelo. Ações para falta de informação, conflito e ausência de consentimento são limitadas pelo runtime; a recomendação livre do modelo fica no trace para inspeção.

Não existem ferramentas de aprovação, envio, exclusão, shell ou troca de planilha. As próximas ações são recomendações registradas para revisão humana.

## Preparar a planilha

Importe [data/relayops-sandbox.xlsx](../data/relayops-sandbox.xlsx) em uma nova planilha Google de teste. Ela contém:

- `Leads`: cabeçalho `id,name,email,budget,horizon_days,consent,message`, seguido de três casos fictícios.
- `AgentReview`: cabeçalho `lead_id,status,summary,next_action,conflict,input_hash,write_id`; linhas de saída inicialmente vazias.

`budget` e `horizon_days` precisam ser números inteiros; `consent` é booleano. Não altere os cabeçalhos. O escopo é de até dez entradas por execução. Nenhum dado de cliente é necessário.

## Execução direta com Google OAuth

Com Ollama instalado e um modelo disponível, configure um access token Google fora do chat e do repositório. O token não é enviado ao modelo.

```bash
ollama pull qwen3:0.6b
# Configure GOOGLE_ACCESS_TOKEN no seu gerenciador de segredos/ambiente local.
python3 scripts/run_agent.py \
  --model qwen3:0.6b \
  --spreadsheet-id SEU_ID_DE_PLANILHA_DE_TESTE \
  --trace runtime/review-001.jsonl \
  --confirm-write
```

Nesta máquina foi usada uma instalação isolada do Ollama em `runtime/ollama-install`, com os modelos em `runtime/ollama-models`. Ela não é versionada. O helper `sh scripts/start_local_model.sh` inicia o servidor local usando o Ollama do PATH ou essa instalação isolada.

O modelo de 0.6B é uma opção leve para demonstração, não uma recomendação universal de qualidade. Para avaliar modelos maiores, mantenha o mesmo conjunto de casos e compare as revisões com uma referência humana.

O token é usado apenas pelo adaptador Sheets. Este projeto não implementa refresh OAuth nem deve receber credenciais por prompt. A gravação usa valores RAW e destino fixo; todas as leituras usam valores não formatados.

## Execução com um conector já autenticado no anfitrião

Quando o acesso ao Google existe em um anfitrião MCP, sem token disponível ao processo Python, há um adaptador IPC explícito:

```bash
python3 scripts/run_agent.py \
  --model qwen3:0.6b \
  --spreadsheet-id SEU_ID_DE_PLANILHA_DE_TESTE \
  --bridge-dir runtime/connector-bridge \
  --trace runtime/review-bridge-001.jsonl \
  --confirm-write
```

O processo publica uma requisição em `runtime/connector-bridge/*.request.json`. O anfitrião deve validar a planilha e o intervalo, executar a operação no seu conector Google e devolver a resposta. Isso é um adaptador de transporte, não uma resposta simulada nem decisão comercial humana.

```bash
python3 scripts/bridge.py runtime/connector-bridge
python3 scripts/bridge.py runtime/connector-bridge \
  --respond ID_DA_REQUISICAO --result-file runtime/provider-result.json
```

O arquivo de resultado contém o objeto retornado pelo provedor, por exemplo `{"values":[["lead_id", "status", ...]]}` para leitura. O helper acrescenta o ID de correlação. O anfitrião não deve alterar o conteúdo ou fabricar sucesso. Para automação independente do anfitrião, use o modo OAuth direto.

A ponte IPC assume um anfitrião confiável; não é autenticação, sandbox de SO nem integração autônoma com qualquer MCP. Ela omite cabeçalhos de autenticação do arquivo. O agente para caso a ponte não responda em dez minutos.

## Evidência e falhas

Cada ação concluída grava ferramenta escolhida, argumentos, retorno, tokens informados pelo Ollama e horário no JSONL. A execução cria um arquivo novo, sem sobrescrever evidências anteriores. Falhas interrompem o fluxo; não há retry cego após gravação ambígua.

A leitura da origem é repetida antes de escrever e ao verificar. Isso detecta mudanças entre observações, mas não implementa compare-and-swap atômico em Sheets: existe uma janela de concorrência. Use um sandbox com um único escritor. Em produção, adote controle transacional e identidade de operador.

Dados e textos do LLM ficam na planilha e no trace; use apenas dados sintéticos na demonstração pública. O trace não registra tokens OAuth ou cabeçalhos. Custo local de CPU/energia não é medido.

### Contrato do anfitrião da ponte

1. Aceitar apenas `https://sheets.googleapis.com/v4/spreadsheets/<ID_CONFIGURADO>/values/...`.
2. Para GET, permitir `Leads!A1:G11`, `AgentReview!A1:G1` e linhas individuais de `AgentReview!A2:G11`. Usar valores não formatados.
3. Para PUT, aceitar uma única linha com sete valores em `AgentReview!A2:G11`. O adaptador do anfitrião pode mapear isso para `updateCells` com `fields=userEnteredValue`, preservando formato e valores fora do alvo. Strings devem ser escritas como stringValue, não fórmulas.
4. Conferir metadados e as células do destino antes da primeira alteração; preservar validações e cabeçalhos. Não oferecer escrita em Leads.
5. Retornar a resposta real, correlacionada pelo ID. Não editar avaliações do modelo na ponte. Se o conector falhar, devolver erro e encerrar a execução.

A execução direta com OAuth usa a API values do Google. A execução com ponte usa o conector do anfitrião. São dois transportes distintos; testar a ponte não comprova login ou refresh OAuth do processo Python.
