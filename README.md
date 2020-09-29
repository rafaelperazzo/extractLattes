# extractLattes
**uma ferramenta de extração de informações do currículo lattes**
## Requisitos

* Docker
* Docker-compose

## Entrada

* pasta com os XML Lattes a serem extraídos
* configuração do arquivo config.ini (exemplo):

```
    [DEFAULT]
    inicio = 2013
    fim = 2020
    prefixo = DOCENTES_
    xml_dir = xml/
```
## Saída

* arquivos CSV com as extrações:
 * Produção Bibliográfica
  * Em periódicos
  * Em anais
  * Livros e capítulos
 * Projetos de pesquisa
 * Titulação
 * Títulos

## Como executar

```
docker-compose run --rm scorelattes python scorerun.py
```

## TODO
* Adicionar geolocalização
* Incluir outras extrações, como vínculos profissionais e projetos de extensão

## AGRADECIMENTOS

Ao projeto do Prof. Vicente Helano (UFCA) [scoreLattes](https://github.com/vicentehelano/scoreLattes)