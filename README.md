# 🎮 GameRadar — Jogos físicos novos e usados

Aplicativo PWA para Android e desktop, com monitoramento por **fontes autorizadas**, filtros, favoritos, detecção de anúncios novos e quedas de preço. Desenvolvido com **Python 3.11+ e JavaScript sem dependências externas**.

## Funcionalidades prontas

- Painel em português responsivo para instalação como app Android.
- Buscar por título, filtrar consoles, condição, preço, região e fonte; ordenar e favoritar (no navegador).
- Coleta JSON / RSS / Atom **autorizados pelo fornecedor**; inventário de vendedores Mercado Livre que deram permissão OAuth ao aplicativo.
- Registro histórico com ID estável, uma primeira coleta silenciosa por fonte, alertas de novos anúncios e quedas significativas.
- Notificações via ntfy com **um digest por rodada** e fila que tenta novamente quando falha.
- CI, workflows de coleta programada (uma vez por hora) e publicação opcional pelo GitHub Pages.
- Modo demonstração explícito com três anúncios fictícios; os dados reais iniciam vazios.

**NÃO** há busca pública geral implementada na Amazon, Mercado Livre, Shopee ou OLX. Os conectores dependem de permissões e contratos: não usamos scraping nem APIs não documentadas. "Todos os jogos" significa **todos os jogos de console reconhecidos nos feeds cadastrados**, não o catálogo inteiro da internet. Alguns anúncios podem ser classificados erroneamente conforme o título.

## Rodar localmente

    python -m unittest discover -s tests -v
    python -m gameradar.core collect
    cp data/feed.json site/data/feed.json
    python -m http.server 8000 --directory site

Abra http://localhost:8000 no computador ou navegador Termux. Não é necessário instalar bibliotecas extras no Python.

## Configurar fontes reais

Edite config/sources.json. Exemplo de estrutura **não funcional**, apenas para configurar uma loja que permita exportar seus anúncios:

    {
      "feeds": [
        {
          "id": "loja_parceira",
          "name": "Loja Parceira",
          "url": "https://loja-parceira.example/feeds/games.json",
          "format": "json",
          "enabled": true,
          "currency": "BRL",
          "condition_hint": "new"
        }
      ],
      "mercadolivre_sellers": []
    }

Cada item JSON deve ter id, title, price, url HTTPS; opcionalmente image, condition ("new" ou "used"), location, shipping e currency. Aceita objeto com items[] ou array. O título deve identificar Nintendo Switch, Switch 2, PS4, PS5, Xbox One ou Xbox Series; se não identificar, use platform_hint na fonte. IDs precisam permanecer estáveis. Feeds RSS/Atom precisam ter preço em g:price/g:sale_price ou texto como R$ 199,90 na descrição. Limite por feed 1500 registros por execução.

Para fontes protegidas, use a propriedade token_env com o **nome** de uma variável de ambiente secreta (Bearer token); configure esse Secret no GitHub, nunca salve o token no JSON.

### Mercado Livre

A API oficial permite listar inventário de **vendedores autorizados** por /users/{seller_id}/items/search e /items/bulk. Coloque um ou mais IDs numéricos em mercadolivre_sellers e configure o secret ML_ACCESS_TOKEN. **O token expira em cerca de 6 horas e este projeto não renova automaticamente a sessão OAuth**. Para serviço contínuo, é necessário implantar fluxo seguro de OAuth e renovação de refresh token com rotação. Não tente substituir por /sites/MLB/search: busca ampla pode estar restrita a apps autorizados.

### OLX / Shopee / Amazon

Sem conexão de busca geral. APIs da OLX para anúncios se destinam ao anunciante; Shopee e Amazon requerem acesso apropriado. Use feeds parceiros com permissão expressa. Não inclua páginas HTML ou endpoints internos para contornar restrições.

## Notificações no Android

1. Instale o ntfy (https://ntfy.sh/) no seu aparelho.
2. Gere tópico difícil de adivinhar no Termux/PC com: python -c "import secrets;print('gameradar-'+secrets.token_urlsafe(24))"
3. Inscreva-se nesse tópico no ntfy.
4. No GitHub: Settings → Secrets and variables → Actions → New repository secret, cadastre NTFY_TOPIC com esse tópico.
5. Em config/rules.json edite consoles, condições, preço máximo, palavras incluídas/excluídas, filtro de fontes e mínimos de queda. A interface permite **exportar** o JSON com as seleções, mas não altera diretamente o servidor.

Tópicos públicos ntfy não são privados se o nome vazar. Se nenhuma fonte/NTFY_TOPIC está configurado, não haverá notificações. Primeiro scan de cada fonte é silencioso. A fila é persistida antes do envio e confirmada depois; interrupções neste intervalo **podem causar reenvios**. Os alertas são enviados em lotes de até 10 ofertas resumidas por mensagem, com contagem das demais. ntfy público possui limites de uso.

## Publicar no GitHub Pages (PWA instalável no Android)

O repositório **já está público**; a publicação do site depende de habilitar Pages uma vez.

1. No celular, abra [Settings → Pages](https://github.com/Gabriel-Liz2003/GameRadar/settings/pages).
2. Em **Build and deployment → Source**, selecione **GitHub Actions**. Não crie workflow por modelo: o projeto já tem o arquivo `.github/workflows/monitor.yml`.
3. Em [Actions → GameRadar • monitor](https://github.com/Gabriel-Liz2003/GameRadar/actions/workflows/monitor.yml), selecione **Run workflow → main → Run workflow**. O monitor detecta Pages habilitado e publica a interface automaticamente.
4. Após o deploy bem-sucedido, abra o link informado em Settings → Pages. Endereço habitual: https://gabriel-liz2003.github.io/GameRadar/ (confirme que já existe antes de compartilhar).
5. No Chrome/Brave Android, menu → **Instalar aplicativo / Adicionar à tela inicial**.

**Não é necessário criar `ENABLE_PAGES` nem guardar tokens para publicar o site.** Pages fica desativado enquanto a conta não selecionar a fonte de publicação; o monitor detecta isso e ignora o deploy sem impedir as coletas.

O monitor é agendado para uma execução por hora (o GitHub pode atrasar ou suspender horários). Apenas as fontes autorizadas configuradas produzirão ofertas reais; enquanto vazias, o app exibirá estado vazio e um botão de exemplos fictícios. Os dados enviados ao site ficarão públicos.

## Segurança e arquitetura

- config/sources.json: feeds aprovados / vendedores autorizados
- config/rules.json: filtros de notificações automáticas
- gameradar/core.py: coleta, normalização, histórico, filtros, fila, notificação ntfy
- data/state.json: estado persistente (não editar) e data/feed.json: snapshots públicos
- site/: interface PWA estática, sem tokens
- .github/workflows/monitor.yml: coleta + push de dados + deploy opcional
- .github/workflows/test.yml: testes e validação
- tests/: testes determinísticos sem rede

A interface não possui autenticação de usuário nem backend interativo: preferências e favoritos ficam apenas no dispositivo, enquanto a automação roda nas configurações do repositório. A coleta conserva até 15 mil IDs históricos e exibe até 1.500 registros.
