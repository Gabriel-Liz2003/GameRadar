# GameRadar — somente jogos físicos Nintendo Switch e Switch 2

**Aplicativo:** https://gabriel-liz2003.github.io/GameRadar/

O radar busca anúncios de **jogos físicos** de Nintendo Switch e Switch 2, novos, usados e de condição não informada. Descarta consoles, controles, acessórios, DLCs digitais e contas de jogos. É um PWA instalável no Android, com coleta agendada pelo GitHub Actions e alertas via ntfy.

**Status de verdade:** código e automação estão implementados; **as lojas só enviarão anúncios depois que suas integrações autorizadas estiverem conectadas**. O projeto não pesquisa todos os anúncios de todas as lojas de forma anônima. O painel mostra um aviso de configuração enquanto não há fontes reais.

## 1. Ativar a busca automática de jogos físicos na Shopee

O conector Shopee Affiliate GraphQL já está no backend e habilitado em `config/sources.json`. Ele pesquisa jogos de Switch e Switch 2 em seis termos e filtra títulos para reter apenas jogos físicos. Busca apenas **ofertas disponíveis para a API de Afiliados**, não o catálogo inteiro da Shopee.

**Requisitos:**
1. Ter conta no Programa de Afiliados da Shopee Brasil: https://affiliate.shopee.com.br/
2. Solicitar e receber **acesso à Open API de Afiliados**, que pode depender de aprovação. Login Shopee comum não basta.
3. Obter **App ID** e **App Secret**. Não coloque credenciais em arquivos públicos.
4. No GitHub, abra https://github.com/Gabriel-Liz2003/GameRadar/settings/secrets/actions e use **New repository secret** para criar:
   - `SHOPEE_APP_ID` — App ID
   - `SHOPEE_APP_SECRET` — App Secret
5. Execute **Actions → GameRadar • monitor → Run workflow**, na branch main: https://github.com/Gabriel-Liz2003/GameRadar/actions/workflows/monitor.yml
6. Quando a Shopee responder à consulta, os jogos aparecerão no aplicativo. **A primeira coleta é silenciosa**, para não alertar sobre centenas de anúncios antigos. Depois, novos anúncios e quedas de preço entram na fila de alertas.

**Atenção:** não tenho credenciais e não posso solicitar o acesso em seu nome. A API pode retornar erro 10035 (acesso não aprovado), 10030 (limite) ou 10020 (assinatura inválida). Erros aparecem no diagnóstico do monitor.

Documentação baseada na API pública (**site de terceiros, confirme com a Shopee**): https://www.affiliateshopee.com.br/documentacao
Explorer: https://open-api.affiliate.shopee.com.br/explorer

O arquivo `config/sources.json` já contém os termos:
- jogo nintendo switch 2
- jogo nintendo switch
- mario kart switch
- pokemon switch
- zelda switch
- kirby switch

Você pode ampliar os termos (até 12) e configurar o número de páginas (até cinco). O monitor não promete cobrir todo o catálogo e pode ter resultados parciais conforme a API.

## 2. Ativar notificações no Android

1. Instale o app **ntfy** (https://ntfy.sh/) no Android.
2. Gere um tópico longo e aleatório no Termux: `python -c "import secrets;print('gameradar-'+secrets.token_urlsafe(24))"`
3. Inscreva-se nesse tópico dentro do ntfy.
4. Em https://github.com/Gabriel-Liz2003/GameRadar/settings/secrets/actions, cadastre o secret `NTFY_TOPIC` com esse nome.
5. Em `config/rules.json`, ajuste filtros de console, preço, palavras e quedas mínimas. O site permite exportar o JSON para substituir no GitHub, mas a mudança do painel **não atualiza automaticamente os alertas do backend**.

Uma única notificação resume até dez ofertas e indica quantas adicionais existem. O envio falhou? O sistema guarda a fila para outra tentativa; duplicação ainda é possível se a execução interromper após o envio e antes da confirmação. Sem tópico ntfy, a fila é esvaziada sem notificar.

**Privacidade:** o serviço público ntfy.sh não oferece privacidade automática para tópicos adivinháveis; use tópico aleatório e não o compartilhe.

## 3. Mercado Livre, OLX, Amazon e lojas

- **Mercado Livre:** o backend permite `mercadolivre_sellers` (IDs de vendedores autorizados) e `mercadolivre_items` (IDs de produtos acompanhados), usando `ML_ACCESS_TOKEN` no Actions Secret. A autorização OAuth é obrigatória e o token expira; a aplicação **não renova refresh tokens sozinha** e não tem busca geral irrestrita do marketplace. Docs: https://developers.mercadolivre.com.br/pt_br/itens-e-buscas
- **OLX:** a documentação oficial de sua API atende principalmente ao gerenciamento de anúncios do próprio vendedor; sem busca pública ampla integrada: https://developers.olx.com.br/anuncio/api/home.html
- **Amazon:** a Creators API exige conta de Associados, aprovação e credenciais; **não está integrada**: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction
- **Lojas com feeds autorizados:** adicione uma entrada em `feeds` com URL HTTPS, formato `json`, `rss` ou `atom`, ID, nome, e indicação de plataforma somente se o feed for especificamente de Switch/Switch 2. O backend suporta JSON com `items` contendo `id`, `title`, `price`, `url`, `condition`, `image`, `location` e `shipping`. **Não use páginas HTML como feeds**.

Modelo ilustrativo de feed JSON (URL e produto de exemplo, não são reais):

~~~json
{"feeds":[{"id":"loja-parceira","name":"Loja Parceira","url":"https://parceiro.example/catalogo.json","format":"json","enabled":true,"currency":"BRL","complete_snapshot":false}]}
~~~

Não marque `complete_snapshot:true` em fontes de resultados parciais ou páginas de buscas. Isso marcaria como indisponíveis jogos que ainda existem.

## 4. Como funciona

- Reconhece apenas as plataformas `switch` e `switch2`; filtra consoles, acessórios e itens digitais a partir de títulos. Anúncios vagos podem ser removidos para evitar falsos positivos.
- Se um anúncio de jogo Switch não menciona a plataforma, configure `platform_hint` **somente num feed que garanta essa plataforma**.
- A condição não confirmada é exibida como **Não informada**, e incluída na busca e nos alertas por padrão. A Shopee não entrega condição no exemplo da API de afiliados.
- Histórico por anúncio inclui primeiro preço, menor preço observado e até 25 mudanças. A primeira coleta da fonte não envia alertas antigos.
- O código salva anúncios, condições e links públicos em `data/feed.json` e estado da fila em `data/state.json`. O GitHub Pages publica só o feed, nunca os Secrets.
- Execução aproximadamente horária (GitHub Actions pode atrasar). O preço mostrado não inclui frete quando a API não fornece a informação.
- Se nenhum resultado aparecer, cheque as fontes em `data/feed.json` (campo `health` com `ok`, `needs_setup` ou `error`).
- O objetivo é custo zero dentro dos limites gratuitos de GitHub Actions/Pages e API/ntfy. Provedores podem impor limites próprios.

## 5. Rodar e testar localmente

~~~sh
python -m unittest discover -s tests -v
python -m gameradar.core collect
cp data/feed.json site/data/feed.json
python -m http.server 8000 --directory site
~~~

Python 3.11+ e navegador moderno bastam, sem bibliotecas Python extras.

**Segurança:** não publique App ID Secret, tokens, identificadores ntfy ou dados privados em código/issues públicos. As ofertas no site serão públicas; confirme preços, autenticidade e condições no anúncio original antes de comprar.
