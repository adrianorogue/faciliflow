# FaciliFlow — MVP (Streamlit)

## Rodar local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Publicar no Streamlit Community Cloud (passo a passo)
1) Crie um repositório no GitHub (ex.: `faciliflow`).
2) Faça upload **de todos os arquivos desta pasta** (incluindo `requirements.txt` e a pasta `assets/`).
3) Acesse o Streamlit Community Cloud e clique em **New app**.
4) Selecione:
   - **Repository**: seu repo
   - **Branch**: `main`
   - **Main file path**: `app.py`
5) Clique em **Deploy**.

### Dependências
- O Streamlit Cloud instala as libs listadas em `requirements.txt`.
- Se um pacote nativo do SO for necessário (não é o caso aqui), use `packages.txt`.

### Observação importante sobre dados
Este MVP salva dados em memória/sessão (Streamlit Session State). No Streamlit Cloud, reinícios e novos deploys podem **apagar o estado**. Para produção “de verdade”, o ideal é persistir em um banco (SQLite/Postgres) ou storage.

## Páginas (MVP)
1) **Obras**: mostra uma linha por obra (CT) e permite expandir para editar **etapas** (estilo Monday). As **sequências de produção** ficam em um popover por obra.
2) **Peças**: define capacidade (m³/dia), faz upload com **mapeamento**, consulta com filtros por CT/Etapa/Sequência e permite **exclusão** (seleção/filtro/limpar).
3) **Mix de Produção**: gera mix diário e permite visualizar **Diária/Semanal/Mensal**. Mostra pendências e o gráfico Demanda x Capacidade.

## Observações
- Nesta versão, **não há mapa de formas**, então **não calculamos Qtd de Pistas**.
- A linha **TOTAL** do MIX fica **travada no rodapé** e soma Comprimento Total de Fundo e Volume.
- As tabelas usam **filtro no cabeçalho** (AgGrid).
