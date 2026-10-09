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

## Publicar no GitHub Pages (PWA instalável no celular)

Este repositório foi criado **privado**. O GitHub Pages em contas GitHub Free requer repositório **público**; GitHub Pro/Team/Enterprise pode hospedar sites de repositórios privados, mas o site pode continuar publicamente acessível. Não mudamos a visibilidade por segurança.

1. Com uma conta/plano elegível, entre em Settings → Pages → Build and deployment → Source: GitHub Actions.
2. Em Settings → Secrets and variables → Actions → Variables, crie a variável ENABLE_PAGES igual a true.
3. Em Actions → GameRadar • monitor → Run workflow, execute manualmente.
4. Verifique o endereço gerado na aba Pages; normalmente https://gabriel-liz2003.github.io/GameRadar/.
5. Abra HTTPS no Chrome/Brave Android → menu → Instalar aplicativo / Adicionar à tela inicial.

O workflow agendado pode atrasar e, em repositórios privados, consome minutos gratuitos da conta (custo zero só enquanto dentro das franquias). Também é possível hospedar site/monitor em servidores próprios. Os dados no feed/site publicado tornam-se públicos.

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
